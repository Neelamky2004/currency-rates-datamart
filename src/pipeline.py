"""
Currency Rates Data Mart local ETL and volatility calculation pipeline.
"""
from datetime import datetime
import sqlite3
import pandas as pd


class CurrencyDataMartPipeline:
    """ETL Pipeline for cleaning, analyzing, and persisting FX rates."""

    def __init__(self, db_path: str = "currency_rates.db"):
        self.db_path = db_path

    def clean_rates(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = ['base_currency', 'target_currency', 'exchange_rate']
        clean_df = df.dropna(subset=cols).copy()
        clean_df['exchange_rate'] = pd.to_numeric(clean_df['exchange_rate'], errors='coerce')
        clean_df = clean_df.dropna(subset=['exchange_rate'])
        clean_df = clean_df[clean_df['exchange_rate'] > 0]
        if 'trade_date' not in clean_df.columns or clean_df['trade_date'].isnull().all():
            clean_df['trade_date'] = datetime.utcnow().strftime('%Y-%m-%d')
        return clean_df

    def compute_volatility_metrics(self, df: pd.DataFrame, threshold_std: float = 2.0):
        result = df.copy()
        mean = result['exchange_rate'].mean()
        std = result['exchange_rate'].std()
        if pd.isna(std) or std == 0:
            result['z_score'] = 0.0
            result['spike_flag'] = 0
        else:
            result['z_score'] = (result['exchange_rate'] - mean) / std
            result['spike_flag'] = result['z_score'].abs().apply(
                lambda x: 1 if x >= threshold_std else 0
            )
        return result

    def load_to_datamart(self, df: pd.DataFrame, table_name: str = "fact_currency_rates"):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    target_currency TEXT NOT NULL,
                    exchange_rate REAL NOT NULL,
                    z_score REAL,
                    spike_flag INTEGER NOT NULL
                )
            """)
            cols = [
                'trade_date', 'base_currency', 'target_currency',
                'exchange_rate', 'z_score', 'spike_flag'
            ]
            records = df[cols].to_records(index=False)
            cursor.executemany(f"""
                INSERT INTO {table_name} (
                    trade_date, base_currency, target_currency,
                    exchange_rate, z_score, spike_flag
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, list(records))
            conn.commit()

    def run_pipeline(self, df: pd.DataFrame):
        cleaned = self.clean_rates(df)
        analyzed = self.compute_volatility_metrics(cleaned)
        self.load_to_datamart(analyzed)
        return analyzed
