# pyrefly: ignore [missing-import]
from app.trading.lot_calculator import lot_calculator

def test_lot_size_calculation_accuracy(sample_account, sample_gold_symbol):
    # Entry @ 2650.00, SL @ 2645.00 -> $5.00 distance
    # 1.0 lot loss = 5.00 * 100 oz = $500.00
    # Equity = $10,000, 1% risk = $100.00
    # Expected lot = $100 / $500 = 0.20 lots
    lots = lot_calculator.calculate(
        account=sample_account,
        symbol_info=sample_gold_symbol,
        entry_price=2650.00,
        stop_loss=2645.00,
        risk_percent=1.0
    )
    assert lots == 0.20
