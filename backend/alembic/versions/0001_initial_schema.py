"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-09 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Webhook events
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('event_uuid', sa.String(length=36), nullable=False),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('source_ip', sa.String(length=45), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('processing_status', sa.Enum('RECEIVED', 'VALIDATED', 'DUPLICATE', 'PROCESSED', 'REJECTED', 'FAILED', name='webhookstatus'), nullable=False),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webhook_events_uuid', 'webhook_events', ['event_uuid'], unique=True)
    op.create_index('idx_webhook_events_hash', 'webhook_events', ['payload_hash'])

    # 2. Signals
    op.create_table(
        'signals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('webhook_event_id', sa.BigInteger(), nullable=True),
        sa.Column('signal_uuid', sa.String(length=36), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('action', sa.Enum('BUY', 'SELL', 'CLOSE', 'MODIFY', name='orderside'), nullable=False),
        sa.Column('target_price', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('stop_loss', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('take_profit', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'VALIDATED', 'REJECTED_SESSION', 'REJECTED_RISK', 'REJECTED_DUPLICATE', 'EXECUTED', 'FAILED', name='signalstatus'), nullable=False),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['webhook_event_id'], ['webhook_events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_signals_uuid', 'signals', ['signal_uuid'], unique=True)
    op.create_index('idx_signals_symbol', 'signals', ['symbol'])

    # 3. Orders
    op.create_table(
        'orders',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('signal_id', sa.BigInteger(), nullable=True),
        sa.Column('broker_order_ticket', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('order_type', sa.Enum('BUY', 'SELL', 'CLOSE', 'MODIFY', name='orderside'), nullable=False),
        sa.Column('requested_lots', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('filled_lots', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('requested_price', sa.Numeric(precision=12, scale=5), nullable=False),
        sa.Column('execution_price', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('slippage_points', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('stop_loss', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('take_profit', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('execution_retcode', sa.Integer(), nullable=True),
        sa.Column('execution_status', sa.Enum('PENDING', 'FILLED', 'PARTIAL', 'REJECTED', 'CANCELLED', name='orderstatus'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['signal_id'], ['signals.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_orders_ticket', 'orders', ['broker_order_ticket'], unique=True)

    # 4. Positions
    op.create_table(
        'positions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('broker_position_ticket', sa.BigInteger(), nullable=False),
        sa.Column('opening_order_id', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('side', sa.Enum('LONG', 'SHORT', name='positionside'), nullable=False),
        sa.Column('initial_lots', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('current_lots', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=12, scale=5), nullable=False),
        sa.Column('current_stop_loss', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('current_take_profit', sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column('trailing_step_points', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('status', sa.Enum('OPEN', 'CLOSED', 'PARTIALLY_CLOSED', name='positionstatus'), nullable=False),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['opening_order_id'], ['orders.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_positions_ticket', 'positions', ['broker_position_ticket'], unique=True)

    # 5. Trades
    op.create_table(
        'trades',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('position_id', sa.BigInteger(), nullable=False),
        sa.Column('closing_order_ticket', sa.BigInteger(), nullable=False),
        sa.Column('close_price', sa.Numeric(precision=12, scale=5), nullable=False),
        sa.Column('gross_profit', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('commission', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('swap', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('net_profit', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('pips', sa.Numeric(precision=10, scale=1), nullable=False),
        sa.Column('exit_reason', sa.Enum('TAKE_PROFIT', 'STOP_LOSS', 'TRAILING_STOP', 'SIGNAL_CLOSE', 'EMERGENCY_STOP', 'MANUAL', name='exitreason'), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['position_id'], ['positions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Account Snapshots
    op.create_table(
        'account_snapshots',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('balance', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('equity', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('margin', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('free_margin', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('margin_level', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('open_positions_count', sa.Integer(), nullable=False),
        sa.Column('daily_realized_pnl', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('daily_floating_pnl', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Risk Events
    op.create_table(
        'risk_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('signal_id', sa.BigInteger(), nullable=True),
        sa.Column('event_type', sa.Enum('DAILY_LOSS_BREACH', 'MAX_DRAWDOWN_LIMIT', 'SPREAD_EXCEEDED', 'CONSECUTIVE_LOSS_PAUSE', 'INVALID_LOT_SIZE', 'MARGIN_CALL_PROTECT', 'BOT_STATE_RESTRICTION', name='riskeventtype'), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('threshold_value', sa.String(length=50), nullable=False),
        sa.Column('actual_value', sa.String(length=50), nullable=False),
        sa.Column('system_action_taken', sa.Enum('SIGNAL_REJECTED', 'BOT_PAUSED', 'EMERGENCY_STOP_TRIGGERED', name='riskaction'), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['signal_id'], ['signals.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. Audit & Settings
    op.create_table(
        'bot_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('previous_state', sa.String(length=30), nullable=True),
        sa.Column('new_state', sa.String(length=30), nullable=True),
        sa.Column('triggered_by', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'system_settings',
        sa.Column('key_name', sa.String(length=100), nullable=False),
        sa.Column('config_value', sa.JSON(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('key_name')
    )

    # 9. Trading Sessions
    op.create_table(
        'trading_sessions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_name', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('start_time_utc', sa.Time(), nullable=False),
        sa.Column('end_time_utc', sa.Time(), nullable=False),
        sa.Column('max_allowed_spread_points', sa.Numeric(precision=8, scale=2), nullable=False, server_default='35.00'),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trading_sessions_name', 'trading_sessions', ['session_name'], unique=True)

    # 10. Strategy Configurations
    op.create_table(
        'strategy_configs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('strategy_name', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False, server_default='XAUUSD'),
        sa.Column('timeframe', sa.String(length=10), nullable=False, server_default='M15'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('risk_percent', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.00'),
        sa.Column('max_positions', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('max_daily_loss_percent', sa.Numeric(precision=5, scale=2), nullable=False, server_default='3.00'),
        sa.Column('max_spread_points', sa.Numeric(precision=8, scale=2), nullable=False, server_default='35.00'),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_strategy_configs_name', 'strategy_configs', ['strategy_name'], unique=True)
    op.create_index('idx_strategy_configs_symbol', 'strategy_configs', ['symbol'])

def downgrade() -> None:
    op.drop_table('strategy_configs')
    op.drop_table('trading_sessions')
    op.drop_table('system_settings')
    op.drop_table('bot_events')
    op.drop_table('risk_events')
    op.drop_table('account_snapshots')
    op.drop_table('trades')
    op.drop_table('positions')
    op.drop_table('orders')
    op.drop_table('signals')
    op.drop_table('webhook_events')
