import pandas as pd
from sklearn.ensemble import IsolationForest


class FXAnomalyDetector:
    """Unsupervised anomaly detector for FX volatility regimes."""

    def __init__(self, contamination: float = 0.15, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=50
        )

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data['exchange_rate'] = pd.to_numeric(data['exchange_rate'], errors='coerce')
        data = data.dropna(subset=['exchange_rate'])
        data['rate_pct_change'] = data['exchange_rate'].pct_change().fillna(0.0)
        data['rolling_std_3'] = (
            data['exchange_rate'].rolling(window=3, min_periods=1).std().fillna(0.0)
        )
        return data

    def fit_predict(self, df: pd.DataFrame):
        data = self.extract_features(df)
        features = data[['exchange_rate', 'rate_pct_change', 'rolling_std_3']]
        predictions = self.model.fit_predict(features)
        data['ml_outlier_flag'] = (predictions == -1).astype(int)
        outlier_count = int(data['ml_outlier_flag'].sum())
        return data, outlier_count
