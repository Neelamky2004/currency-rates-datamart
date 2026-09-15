"""
Supervised machine learning pipeline for FX volatility regime classification
using Scikit-learn RandomForestClassifier.
"""
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer sequential temporal features for exchange rate volatility:
    - lag_1: Prior period exchange rate
    - rate_diff: Absolute day-over-day movement
    - pct_change: Relative percentage change
    - rolling_std_3: Short-term rolling volatility window
    """
    data = df.copy()
    data['exchange_rate'] = pd.to_numeric(data['exchange_rate'], errors='coerce')
    data = data.dropna(subset=['exchange_rate']).sort_values('trade_date').reset_index(drop=True)

    data['lag_1'] = data['exchange_rate'].shift(1).fillna(data['exchange_rate'])
    data['rate_diff'] = data['exchange_rate'] - data['lag_1']
    data['pct_change'] = (data['rate_diff'] / data['lag_1'].replace(0, np.nan)).fillna(0.0)
    data['rolling_std_3'] = (
        data['exchange_rate'].rolling(window=3, min_periods=1).std().fillna(0.0)
    )

    mean_rate = data['exchange_rate'].mean()
    std_rate = data['exchange_rate'].std()
    threshold = mean_rate + (1.25 * (std_rate if (pd.notna(std_rate) and std_rate > 0) else 1.0))
    data['volatility_regime'] = (data['exchange_rate'] >= threshold).astype(int)

    return data


def train_volatility_classifier(
    csv_path: str = "data/sample_fx_rates.csv",
    test_size: float = 0.25
) -> Tuple[RandomForestClassifier, Dict[str, float]]:
    """
    Trains a RandomForestClassifier using chronological time-series splitting
    to evaluate volatility prediction without lookahead bias.
    """
    df = pd.read_csv(csv_path)
    engineered = extract_features(df)

    feature_cols = ['exchange_rate', 'lag_1', 'rate_diff', 'pct_change', 'rolling_std_3']
    X = engineered[feature_cols]
    y = engineered['volatility_regime']

    split_idx = int(len(X) * (1.0 - test_size))
    if split_idx >= len(X):
        split_idx = max(1, len(X) - 2)

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    clf = RandomForestClassifier(
        n_estimators=50,
        max_depth=4,
        random_state=42
    )
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = float(accuracy_score(y_test, preds))
    prec = float(precision_score(y_test, preds, zero_division=0))

    metrics = {
        'accuracy': acc,
        'precision': prec,
        'train_samples': len(X_train),
        'test_samples': len(X_test)
    }
    return clf, metrics


if __name__ == "__main__":
    model, eval_metrics = train_volatility_classifier()
    print("[TRAINING COMPLETE]")
    print(f"Accuracy:  {eval_metrics['accuracy'] * 100:.2f}%")
    print(f"Precision: {eval_metrics['precision'] * 100:.2f}%")
