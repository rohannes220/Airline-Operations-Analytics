"""Compare pre-departure delay classifiers without using future flights for tuning."""
import json
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from src.config import DATABASE_URL, MODEL_DIR

FEATURES = ['airline', 'origin', 'destination', 'month', 'day_of_week',
            'departure_hour', 'distance', 'is_weekend', 'scheduled_elapsed_time']
CAT = ['airline', 'origin', 'destination']
NUM = [x for x in FEATURES if x not in CAT]
THRESHOLDS = np.arange(0.20, 0.81, 0.05)


def preprocessing():
    return ColumnTransformer([
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ]), CAT),
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scale', StandardScaler())
        ]), NUM),
    ])


def evaluate(y, predictions, probabilities):
    result = {
        'accuracy': round(accuracy_score(y, predictions), 4),
        'precision': round(precision_score(y, predictions, zero_division=0), 4),
        'recall': round(recall_score(y, predictions, zero_division=0), 4),
        'f1': round(f1_score(y, predictions, zero_division=0), 4),
        'roc_auc': round(roc_auc_score(y, probabilities), 4) if len(np.unique(y)) > 1 else None,
    }
    return result


def train(database_url=DATABASE_URL):
    engine = create_engine(database_url)
    df = pd.read_sql(
        'SELECT * FROM fact_flights WHERE cancelled = 0 AND diverted = 0', engine
    )
    df['flight_date'] = pd.to_datetime(df['flight_date'])
    df = df.dropna(subset=['arrival_delayed_15']).sort_values('flight_date')
    if len(df) < 100:
        raise ValueError('Need at least 100 usable flights to train model.')

    # Chronological train / validation / test: 60% / 20% / 20%.
    n = len(df)
    train_df = df.iloc[:int(n * 0.6)]
    val_df = df.iloc[int(n * 0.6):int(n * 0.8)]
    test_df = df.iloc[int(n * 0.8):]
    X_train, y_train = train_df[FEATURES], train_df['arrival_delayed_15'].astype(int)
    X_val, y_val = val_df[FEATURES], val_df['arrival_delayed_15'].astype(int)
    X_test, y_test = test_df[FEATURES], test_df['arrival_delayed_15'].astype(int)

    candidates = {
        'majority_class': Pipeline([
            ('prep', preprocessing()), ('clf', DummyClassifier(strategy='most_frequent'))
        ]),
        'logistic_regression': Pipeline([
            ('prep', preprocessing()), ('clf', LogisticRegression(max_iter=1000))
        ]),
        'logistic_regression_balanced': Pipeline([
            ('prep', preprocessing()),
            ('clf', LogisticRegression(max_iter=1000, class_weight='balanced'))
        ]),
        'random_forest': Pipeline([
            ('prep', preprocessing()),
            ('clf', RandomForestClassifier(
                n_estimators=150, min_samples_leaf=5, max_features='sqrt',
                random_state=42, n_jobs=-1
            ))
        ]),
    }

    validation_results = {}
    fitted = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        probabilities = model.predict_proba(X_val)[:, 1]
        # Choose threshold only using validation data; never tune on test.
        choices = []
        for threshold in ([0.5] if name == 'majority_class' else THRESHOLDS):
            predictions = (probabilities >= threshold).astype(int)
            scores = evaluate(y_val, predictions, probabilities)
            choices.append((scores['f1'], -abs(float(threshold) - 0.5),
                            float(threshold), scores))
        _, _, threshold, scores = max(choices)
        validation_results[name] = {'threshold': round(threshold, 2), **scores}
        fitted[name] = model

    # Primary selection metric: validation F1. Break ties toward simpler models.
    ranking = list(candidates)
    winner = max(ranking, key=lambda name: (
        validation_results[name]['f1'], -ranking.index(name)
    ))
    chosen = fitted[winner]
    threshold = validation_results[winner]['threshold']
    test_probabilities = chosen.predict_proba(X_test)[:, 1]
    test_predictions = (test_probabilities >= threshold).astype(int)

    result = {
        'rows_train': len(train_df),
        'rows_validation': len(val_df),
        'rows_test': len(test_df),
        'positive_rate_train': round(float(y_train.mean()), 4),
        'selection_metric': 'validation_f1',
        'validation_models': validation_results,
        'selected_model': winner,
        'selected_threshold': threshold,
        'test_metrics': evaluate(y_test, test_predictions, test_probabilities),
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(chosen, MODEL_DIR / 'delay_model.joblib')
    (MODEL_DIR / 'metrics.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--database-url', default=DATABASE_URL,
                        help='SQLAlchemy URL; use a synthetic database only for smoke tests')
    args = parser.parse_args()
    train(args.database_url)
