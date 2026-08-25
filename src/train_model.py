"""Train an interpretable pre-departure classifier for 15+ minute arrival delay."""
import json
import joblib
import pandas as pd
from sqlalchemy import create_engine
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from src.config import DATABASE_URL, MODEL_DIR

FEATURES = ['airline','origin','destination','month','day_of_week','departure_hour','distance','is_weekend','scheduled_elapsed_time']
CAT = ['airline','origin','destination']
NUM = [x for x in FEATURES if x not in CAT]

def train(database_url=DATABASE_URL):
    engine = create_engine(database_url)
    df = pd.read_sql('SELECT * FROM fact_flights WHERE cancelled = 0 AND diverted = 0', engine)
    df['flight_date'] = pd.to_datetime(df['flight_date'])
    df = df.dropna(subset=['arrival_delayed_15']).sort_values('flight_date')
    if len(df) < 100:
        raise ValueError('Need at least 100 usable flights to train model.')
    split = int(len(df) * .8)
    train_df, test_df = df.iloc[:split], df.iloc[split:]
    X_train, y_train = train_df[FEATURES], train_df['arrival_delayed_15'].astype(int)
    X_test, y_test = test_df[FEATURES], test_df['arrival_delayed_15'].astype(int)
    prep = ColumnTransformer([
        ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('onehot', OneHotEncoder(handle_unknown='ignore'))]), CAT),
        ('num', Pipeline([('imputer', SimpleImputer(strategy='median')), ('scale', StandardScaler())]), NUM),
    ])
    model = Pipeline([('prep', prep), ('clf', LogisticRegression(max_iter=1000, class_weight='balanced'))])
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]
    metrics = {
        'rows_train': len(train_df), 'rows_test': len(test_df),
        'accuracy': round(accuracy_score(y_test, pred), 4),
        'precision': round(precision_score(y_test, pred, zero_division=0), 4),
        'recall': round(recall_score(y_test, pred, zero_division=0), 4),
        'f1': round(f1_score(y_test, pred, zero_division=0), 4),
        'roc_auc': round(roc_auc_score(y_test, prob), 4) if y_test.nunique() > 1 else None,
    }
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_DIR / 'delay_model.joblib')
    (MODEL_DIR / 'metrics.json').write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    return metrics

if __name__ == '__main__': train()
