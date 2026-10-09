import pytest
from app.brokers.mock_broker import MockBrokerAdapter
from app.schemas.account import AccountInfoDTO, SymbolInfoDTO
from app.trading.risk_engine import RiskEngine

@pytest.fixture
def mock_broker():
    return MockBrokerAdapter()

@pytest.fixture
def risk_engine(mock_broker):
    return RiskEngine(mock_broker)

@pytest.fixture
def sample_account():
    return AccountInfoDTO(
        login=123456,
        balance=10000.0,
        equity=10000.0,
        margin=0.0,
        free_margin=10000.0,
        margin_level=1000.0,
        currency="USD",
        server="TestServer"
    )

@pytest.fixture
def sample_gold_symbol():
    return SymbolInfoDTO(
        name="XAUUSD",
        point=0.01,
        digits=2,
        spread_points=18.0,
        bid=2650.00,
        ask=2650.20,
        lot_min=0.01,
        lot_max=20.0,
        lot_step=0.01,
        trade_contract_size=100.0
    )
