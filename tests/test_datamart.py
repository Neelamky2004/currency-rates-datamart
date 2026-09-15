import sqlite3
from moto import mock_aws
import pandas as pd
import pytest
from src.anomaly_detector import FXAnomalyDetector
from src.cloud_storage import AWSS3DataLakeManager
from src.pipeline import CurrencyDataMartPipeline
from src.train_model import extract_features, train_volatility_classifier


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


def test_ml_feature_engineering_pipeline():
    sample_data = pd.DataFrame({
        'trade_date': ['2026-09-10', '2026-09-11', '2026-09-12', '2026-09-13'],
        'exchange_rate': [83.0, 83.5, 84.0, 86.0]
    })
    fe = extract_features(sample_data)
    assert 'lag_1' in fe.columns
    assert 'rate_diff' in fe.columns
    assert 'pct_change' in fe.columns
    assert 'rolling_std_3' in fe.columns
    assert 'volatility_regime' in fe.columns
    assert len(fe) == 4
    assert fe.loc[1, 'rate_diff'] == pytest.approx(0.5)


def test_random_forest_training_and_evaluation(tmp_path):
    csv_file = tmp_path / "test_rates.csv"
    csv_file.write_text(
        "trade_date,base_currency,target_currency,exchange_rate\n"
        "2026-09-01,USD,INR,83.0\n"
        "2026-09-02,USD,INR,83.2\n"
        "2026-09-03,USD,INR,83.1\n"
        "2026-09-04,USD,INR,83.4\n"
        "2026-09-05,USD,INR,83.3\n"
        "2026-09-06,USD,INR,83.5\n"
        "2026-09-07,USD,INR,120.0\n"
    )
    clf, metrics = train_volatility_classifier(str(csv_file), test_size=0.28)
    assert clf is not None
    assert 0.0 <= metrics['accuracy'] <= 1.0
    assert 0.0 <= metrics['precision'] <= 1.0


def test_aws_s3_storage_mock(tmp_path):
    with mock_aws():
        manager = AWSS3DataLakeManager(bucket_name="test-rates-bucket")
        manager.s3_client.create_bucket(
            Bucket="test-rates-bucket",
            CreateBucketConfiguration={"LocationConstraint": "ap-south-1"}
        )
        sample_file = tmp_path / "rates.csv"
        sample_file.write_text("trade_date,base,target,rate\n2026-09-15,USD,INR,83.45")
        status = manager.upload_rates_snapshot(str(sample_file), "raw/rates.csv")
        assert status is True
