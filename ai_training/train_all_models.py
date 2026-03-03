import pandas as pd
import numpy as np
import os, joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error

DATA = os.path.join(os.path.dirname(__file__), '..', 'dataset_generator')
OUT  = os.path.join(os.path.dirname(__file__), 'saved_models')
os.makedirs(OUT, exist_ok=True)

def train_severity():
    df = pd.read_csv(os.path.join(DATA, 'severity_data.csv'))
    X  = df[['heart_rate','bp_systolic','oxygen_level','temperature','age']]
    y  = df['label']
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=42)
    m = RandomForestClassifier(n_estimators=100, random_state=42)
    m.fit(Xt, yt)
    acc = accuracy_score(yv, m.predict(Xv))
    joblib.dump(m, os.path.join(OUT, 'severity_model.pkl'))
    print(f"✅ severity_model.pkl  accuracy={acc:.3f}")

def train_discharge():
    df = pd.read_csv(os.path.join(DATA, 'discharge_data.csv'))
    X  = df[['severity','age','diag_code']]
    y  = df['days']
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=42)
    m = GradientBoostingRegressor(n_estimators=100, random_state=42)
    m.fit(Xt, yt)
    mae = mean_absolute_error(yv, m.predict(Xv))
    joblib.dump(m, os.path.join(OUT, 'discharge_model.pkl'))
    print(f"✅ discharge_model.pkl  MAE={mae:.2f} days")

def train_demand():
    df = pd.read_csv(os.path.join(DATA, 'demand_data.csv'))
    X  = df[['day','avg_usage']]
    y  = df['actual_usage']
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=42)
    m = RandomForestRegressor(n_estimators=50, random_state=42)
    m.fit(Xt, yt)
    mae = mean_absolute_error(yv, m.predict(Xv))
    joblib.dump(m, os.path.join(OUT, 'demand_forecast_model.pkl'))
    print(f"✅ demand_forecast_model.pkl  MAE={mae:.2f}")

def train_burnout():
    df = pd.read_csv(os.path.join(DATA, 'burnout_data.csv'))
    X  = df[['avg_hours','avg_patients','overtime_days','total_days']]
    y  = df['risk_level']
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=42)
    m = RandomForestClassifier(n_estimators=100, random_state=42)
    m.fit(Xt, yt)
    acc = accuracy_score(yv, m.predict(Xv))
    joblib.dump(m, os.path.join(OUT, 'burnout_model.pkl'))
    print(f"✅ burnout_model.pkl  accuracy={acc:.3f}")

if __name__ == '__main__':
    print("Training all models...\n")
    train_severity(); train_discharge(); train_demand(); train_burnout()
    print("\n✅ All models saved to ai_training/saved_models/")