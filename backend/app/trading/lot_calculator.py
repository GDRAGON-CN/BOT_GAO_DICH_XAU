import math
from typing import Optional, Tuple
from loguru import logger
# pyrefly: ignore [missing-import]
from app.core.config import settings
# pyrefly: ignore [missing-import]
from app.schemas.account import AccountInfoDTO, SymbolInfoDTO

class LotCalculator:
    """
    Calculates deterministic position volume based on:
    - Account equity and risk percentage
    - Entry and Stop Loss distance
    - Broker symbol contract specifications (trade_contract_size, tick_size, tick_value)
    - Volume constraints (lot_min, lot_max, lot_step)
    
    Never assumes 0.01 lot has the same monetary value across brokers.
    If required information is missing or invalid, rejects computation.
    """

    @staticmethod
    def calculate_lots(
        account: AccountInfoDTO,
        symbol_info: Optional[SymbolInfoDTO],
        entry_price: float,
        stop_loss: Optional[float],
        risk_percent: Optional[float] = None
    ) -> Tuple[Optional[float], Optional[str]]:
        # 1. Validate inputs
        if symbol_info is None:
            return None, "Symbol specifications are unavailable. Cannot guess lot size."

        if not symbol_info.trade_contract_size or symbol_info.trade_contract_size <= 0:
            return None, "Invalid contract size in symbol specifications."

        if not symbol_info.lot_min or symbol_info.lot_min <= 0 or not symbol_info.lot_step or symbol_info.lot_step <= 0:
            return None, "Invalid volume limits (lot_min/lot_step) in symbol specifications."

        if account.equity <= 0:
            return None, f"Insufficient account equity (${account.equity:.2f}) for trading."

        if stop_loss is None or stop_loss <= 0:
            return None, "Stop loss is missing or non-positive. Mandatory for risk-based lot sizing."

        price_distance = abs(entry_price - stop_loss)
        if price_distance < (symbol_info.point or 0.00001):
            return None, "Stop loss distance is too close to entry price."

        # 2. Compute monetary risk amount with strict backend capping
        requested_risk = risk_percent if (risk_percent and risk_percent > 0) else settings.RISK_PERCENT_PER_TRADE
        # Strictly enforce backend maximum risk percentage limit
        risk_pct = min(requested_risk, settings.MAX_RISK_PERCENT_PER_TRADE)
        if requested_risk > settings.MAX_RISK_PERCENT_PER_TRADE:
            logger.warning(
                f"Requested risk {requested_risk}% exceeds max allowable backend risk {settings.MAX_RISK_PERCENT_PER_TRADE}%. "
                f"Safely clamped to {risk_pct}%."
            )
        risk_amount = account.equity * (risk_pct / 100.0)

        # 3. Determine loss per 1.0 standard lot
        # If broker provides tick_size and tick_value, use exact tick math:
        # loss_per_lot = (price_distance / tick_size) * tick_value
        # Otherwise fallback to price_distance * trade_contract_size
        if symbol_info.tick_size and symbol_info.tick_size > 0 and symbol_info.tick_value and symbol_info.tick_value > 0:
            ticks = price_distance / symbol_info.tick_size
            loss_per_lot = ticks * symbol_info.tick_value
        else:
            loss_per_lot = price_distance * symbol_info.trade_contract_size

        if loss_per_lot <= 0:
            return None, "Calculated loss per lot is non-positive."

        # 4. Calculate raw lot size
        raw_lots = risk_amount / loss_per_lot

        # 5. Check against broker bounds and system bounds
        min_allowed = max(settings.MIN_LOT_SIZE, symbol_info.lot_min)
        max_allowed = min(settings.MAX_LOT_SIZE, symbol_info.lot_max)

        if raw_lots < min_allowed:
            # Check if trading at minimum allowed lot would exceed 150% of intended risk amount
            min_lot_loss = min_allowed * loss_per_lot
            if min_lot_loss > (risk_amount * 1.5):
                return None, (
                    f"Account too small: Minimum lot {min_allowed} would risk ${min_lot_loss:.2f}, "
                    f"exceeding target risk ${risk_amount:.2f}."
                )
            clamped_lots = min_allowed
        elif raw_lots > max_allowed:
            clamped_lots = max_allowed
        else:
            clamped_lots = raw_lots

        # 6. Quantize strictly according to broker volume step
        step = symbol_info.lot_step
        steps = math.floor(clamped_lots / step + 1e-9)
        final_lots = round(steps * step, 2)

        if final_lots < min_allowed or final_lots > max_allowed:
            return None, f"Quantized lot size {final_lots} outside allowed range [{min_allowed}, {max_allowed}]."

        return final_lots, None

    @classmethod
    def calculate(
        cls,
        account: AccountInfoDTO,
        symbol_info: SymbolInfoDTO,
        entry_price: float,
        stop_loss: Optional[float],
        risk_percent: Optional[float] = None
    ) -> float:
        """Legacy helper returning float (defaulting to 0.01 if error)."""
        lots, err = cls.calculate_lots(account, symbol_info, entry_price, stop_loss, risk_percent)
        if lots is None:
            logger.warning(f"Lot calculation fallback triggered: {err}")
            return settings.MIN_LOT_SIZE
        return lots

lot_calculator = LotCalculator()

