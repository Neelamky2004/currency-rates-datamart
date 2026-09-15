import pytest
import pandas as pd
import sqlite3
from src.pipeline import CurrencyDataMartPipeline
from src.anomaly_detector import FXAnomalyDetector


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


def test_isolation_forest_anomaly_detection():
    detector = FXAnomalyDetector(contamination=0.2, random_state=42)
    sample_df = pd.DataFrame({
        'exchange_rate': [83.1, 83.15, 83.12, 83.18, 140.50, 83.2, 83.1]
    })
    result_df, outlier_count = detector.fit_predict(sample_df)
    assert 'ml_outlier_flag' in result_df.columns
    assert outlier_count >= 1
    assert result_df.loc[result_df['exchange_rate'] == 140.50, 'ml_outlier_flag'].values[0] == 1
