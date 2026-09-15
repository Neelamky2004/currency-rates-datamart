import pytest
import pandas as pd
import sqlite3
from src.pipeline import CurrencyDataMartPipeline

@pytest.fixture
def temp_db(tmp_path):
    return str(tmp_path / "test_rates.db")

def test_currency_data_cleaning():
    pipeline = CurrencyDataMartPipeline(":memory:")
    raw = pd.DataFrame({
        'base_currency': ['USD', None, 'USD', 'EUR'],
        'target_currency': ['INR', 'INR', 'GBP', 'USD'],
        'exchange_rate': [83.5, 82.1, -1.0, 1.08],
        'trade_date': ['2026-09-15', '2026-09-15', '2026-09-15', '2026-09-15']
    })
    cleaned = pipeline.clean_rates(raw)
    assert len(cleaned) == 2
    assert set(cleaned['target_currency']) == {'INR', 'USD'}

def test_currency_spike_detection():
    pipeline = CurrencyDataMartPipeline(":memory:")
    data = pd.DataFrame({
        'base_currency': ['USD'] * 5,
        'target_currency': ['INR'] * 5,
        'exchange_rate': [83.1, 83.2, 83.0, 83.1, 140.0],
        'trade_date': ['2026-09-15'] * 5
    })
    analyzed = pipeline.compute_volatility_metrics(data, threshold_std=1.5)
    assert analyzed['spike_flag'].sum() == 1
    assert analyzed.iloc[-1]['spike_flag'] == 1

def test_datamart_persistence(temp_db):
    pipeline = CurrencyDataMartPipeline(temp_db)
    data = pd.DataFrame({
        'base_currency': ['USD', 'EUR'],
        'target_currency': ['JPY', 'GBP'],
        'exchange_rate': [155.2, 0.85],
        'trade_date': ['2026-09-15', '2026-09-15']
    })
    pipeline.run_pipeline(data)
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fact_currency_rates")
        assert cursor.fetchone()[0] == 2

def test_ml_model_execution():
    from src.train_model import train_volatility_classifier
    clf = train_volatility_classifier("data/sample_fx_rates.csv")
    assert clf is not None
