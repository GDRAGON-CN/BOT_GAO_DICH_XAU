"""State reconciliation service synchronizing MetaTrader 5 broker state with MySQL database."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Tuple
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.brokers.base import IBrokerAdapter
from app.core.constants import OrderStatus, PositionSide, PositionStatus
from app.models.account import AccountSnapshot
from app.models.audit import BotEvent
from app.models.position import Position
from app.schemas.position import PositionDTO

class ReconciliationService:
    """
    Guarantees state integrity after application restart or unexpected crash.
    Never assumes database state is correct without cross-referencing MT5 broker reality.
    
    Sequence:
    1. Connect to MT5 and verify account accessibility.
    2. Retrieve current live account state & take snapshot.
    3. Retrieve live open positions from MT5.
    4. Query open positions recorded in MySQL.
    5. Compare differences:
       - Position open in DB but closed on MT5 (e.g. Stop Loss hit while offline).
       - Position open on MT5 but missing in DB (e.g. manual intervention on terminal).
    6. Reconcile states and persist audit events into bot_events.
    """

    def __init__(self, broker: IBrokerAdapter):
        self.broker = broker

    async def run_reconciliation(self, db: AsyncSession) -> Dict[str, any]:
        logger.info("==================================================")
        logger.info("STARTING POST-STARTUP MT5 BROKER RECONCILIATION")
        logger.info("==================================================")

        report = {
            "reconciled_at": datetime.utcnow().isoformat(),
            "broker_connected": False,
            "account_login": None,
            "broker_positions_count": 0,
            "db_positions_count": 0,
            "orphaned_db_positions_closed": 0,
            "untracked_broker_positions_imported": 0,
            "events_logged": []
        }

        # 1. Verify connection
        is_conn = await self.broker.is_connected()
        if not is_conn:
            logger.warning("Broker not connected. Skipping reconciliation until connection is established.")
            return report

        report["broker_connected"] = True

        # 2. Retrieve account info and persist snapshot
        try:
            account = await self.broker.get_account_info()
            report["account_login"] = account.login

            snapshot = AccountSnapshot(
                balance=Decimal(str(account.balance)),
                equity=Decimal(str(account.equity)),
                margin=Decimal(str(account.margin)),
                free_margin=Decimal(str(account.free_margin)),
                margin_level=Decimal(str(account.margin_level)) if account.margin_level is not None else None,
                open_positions_count=0,
                daily_realized_pnl=Decimal("0.0"),
                daily_floating_pnl=Decimal(str(account.equity - account.balance)),
                captured_at=datetime.utcnow()
            )
            db.add(snapshot)

            # Record telemetry account sync
            from app.monitoring.telemetry import telemetry
            telemetry.record_account_sync()
        except Exception as e:
            logger.error(f"Failed to fetch account info during reconciliation: {e}")
            return report

        # 3. Retrieve live broker open positions
        broker_positions: List[PositionDTO] = await self.broker.get_open_positions()
        report["broker_positions_count"] = len(broker_positions)
        broker_pos_by_ticket: Dict[int, PositionDTO] = {p.ticket: p for p in broker_positions}

        # 4. Retrieve open positions in DB
        db_stmt = select(Position).where(Position.status == PositionStatus.OPEN)
        db_res = await db.execute(db_stmt)
        db_open_positions: List[Position] = list(db_res.scalars().all())
        report["db_positions_count"] = len(db_open_positions)
        db_pos_by_ticket: Dict[int, Position] = {p.broker_position_ticket: p for p in db_open_positions}

        # 5. Check Case A: Position OPEN in DB but NOT on broker MT5
        # (Likely hit Stop Loss / Take Profit / Manual close while bot was offline)
        from app.notifications.telegram_bot import telegram_bot
        for ticket, db_pos in db_pos_by_ticket.items():
            if ticket not in broker_pos_by_ticket:
                logger.warning(f"Reconciliation: DB position #{ticket} is closed on MT5. Updating DB state to CLOSED.")
                db_pos.status = PositionStatus.CLOSED
                db_pos.closed_at = datetime.utcnow()
                report["orphaned_db_positions_closed"] += 1

                evt = BotEvent(
                    event_category="RECONCILIATION",
                    previous_state="OPEN",
                    new_state="CLOSED",
                    triggered_by="RECONCILIATION_ENGINE",
                    message=f"Ticket #{ticket} ({db_pos.symbol}) closed on MT5 while bot was offline. Reconciled to CLOSED.",
                    created_at=datetime.utcnow()
                )
                db.add(evt)
                report["events_logged"].append(f"Closed orphaned ticket #{ticket}")

                # Telegram position closed notification
                close_price = float(db_pos.entry_price) if db_pos.entry_price is not None else 0.0
                telegram_bot.notify_position_closed(
                    ticket=ticket,
                    symbol=db_pos.symbol,
                    close_price=close_price,
                    profit=0.0,
                    reason="OFFLINE_CLOSE_RECONCILED"
                )



        # 6. Check Case B: Position OPEN on broker MT5 but NOT recorded as OPEN in DB
        # (Could be opened manually or crash occurred after MT5 execution before DB commit)
        for ticket, broker_pos in broker_pos_by_ticket.items():
            if ticket not in db_pos_by_ticket:
                logger.warning(
                    f"Reconciliation: Broker position #{ticket} ({broker_pos.symbol}) untracked in DB open list. "
                    f"Importing into DB as OPEN position to prevent duplicate retry/orders."
                )
                side_enum = PositionSide.LONG if str(broker_pos.side).upper() in ("BUY", "LONG", "0") else PositionSide.SHORT
                imported_pos = Position(
                    broker_position_ticket=ticket,
                    opening_order_id=None,
                    symbol=broker_pos.symbol,
                    side=side_enum,
                    initial_lots=Decimal(str(broker_pos.lots)),
                    current_lots=Decimal(str(broker_pos.lots)),
                    entry_price=Decimal(str(broker_pos.entry_price)),
                    current_stop_loss=Decimal(str(broker_pos.stop_loss)) if broker_pos.stop_loss else None,
                    current_take_profit=Decimal(str(broker_pos.take_profit)) if broker_pos.take_profit else None,
                    status=PositionStatus.OPEN,
                    opened_at=datetime.utcnow()
                )
                db.add(imported_pos)

                evt = BotEvent(
                    event_category="RECONCILIATION",
                    previous_state="UNKNOWN",
                    new_state="IMPORTED_TO_DB",
                    triggered_by="RECONCILIATION_ENGINE",
                    message=(
                        f"Imported untracked live MT5 position #{ticket}: {broker_pos.symbol} {broker_pos.side} "
                        f"{broker_pos.lots} lots @ {broker_pos.entry_price} into database."
                    ),
                    created_at=datetime.utcnow()
                )
                db.add(evt)
                report["untracked_broker_positions_imported"] += 1
                report["events_logged"].append(f"Untracked broker position #{ticket} imported into DB")

        await db.commit()
        logger.info(
            f"RECONCILIATION COMPLETED: {report['broker_positions_count']} on MT5, "
            f"{report['orphaned_db_positions_closed']} closed, {report['untracked_broker_positions_imported']} untracked."
        )
        logger.info("==================================================")
        return report
