import pandas as pd
from src.pipeline import CurrencyDataMartPipeline

if __name__ == "__main__":
    print("[INIT]: Loading Currency FX rates batch...")
    df = pd.read_csv("data/sample_fx_rates.csv")
    pipeline = CurrencyDataMartPipeline("currency_rates.db")
    result = pipeline.run_pipeline(df)
    print("[SUCCESS]: FX Data Mart populated successfully.")
    print(result[['trade_date', 'base_currency', 'target_currency', 'exchange_rate', 'spike_flag']])
