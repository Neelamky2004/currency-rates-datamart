import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, classification_report

def train_volatility_classifier(csv_path: str = "data/sample_fx_rates.csv"):
    df = pd.read_csv(csv_path)
    
    # Feature engineering: Synthetic lagged variance & relative shift
    df['lag_1'] = df['exchange_rate'].shift(1).fillna(df['exchange_rate'])
    df['rate_diff'] = df['exchange_rate'] - df['lag_1']
    df['pct_change'] = df['rate_diff'] / df['lag_1']
    
    # Binary classification target: Significant movement flag
    mean = df['exchange_rate'].mean()
    std = df['exchange_rate'].std()
    threshold = mean + (1.5 * (std if std > 0 else 1.0))
    df['target_anomaly'] = (df['exchange_rate'] >= threshold).astype(int)

    X = df[['exchange_rate', 'lag_1', 'rate_diff', 'pct_change']]
    y = df['target_anomaly']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.28, random_state=42)

    clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"[ML PIPELINE] Random Forest Model Trained Successfully.")
    print(f"[METRIC] Evaluation Accuracy: {acc * 100:.2f}%")
    return clf

if __name__ == "__main__":
    train_volatility_classifier()
