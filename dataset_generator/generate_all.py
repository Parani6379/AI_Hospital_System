import pandas as pd
import numpy as np
import os

OUT = os.path.dirname(__file__)

def gen_severity(n=2000):
    np.random.seed(42)
    rows = []
    for _ in range(n):
        hr   = np.random.randint(40, 160)
        bp   = np.random.randint(80, 200)
        o2   = np.random.uniform(80, 100)
        temp = np.random.uniform(35, 41)
        age  = np.random.randint(18, 90)
        score = 0
        if hr > 120 or hr < 45: score += 30
        elif hr > 100:           score += 15
        if o2 < 90:              score += 35
        elif o2 < 94:            score += 20
        if bp > 170:             score += 20
        elif bp > 150:           score += 10
        if temp > 39.5:          score += 15
        elif temp > 38.5:        score += 8
        if age > 70:             score += 10
        score = min(score + np.random.randint(-5, 5), 100)
        label = 1 if score >= 45 else 0
        rows.append([hr, bp, o2, temp, age, score, label])
    df = pd.DataFrame(rows, columns=['heart_rate','bp_systolic','oxygen_level','temperature','age','severity_score','label'])
    df.to_csv(os.path.join(OUT, 'severity_data.csv'), index=False)
    print(f"✅ severity_data.csv ({len(df)} rows)")
    return df

def gen_discharge(n=1500):
    np.random.seed(43)
    rows = []
    for _ in range(n):
        sev  = np.random.uniform(0, 100)
        age  = np.random.randint(18, 90)
        diag = np.random.randint(1, 10)
        base = 3
        if sev >= 75: base = 14
        elif sev >= 45: base = 7
        if age > 65: base += 2
        days = max(1, int(base + np.random.randint(-2, 3)))
        rows.append([sev, age, diag, days])
    df = pd.DataFrame(rows, columns=['severity','age','diag_code','days'])
    df.to_csv(os.path.join(OUT, 'discharge_data.csv'), index=False)
    print(f"✅ discharge_data.csv ({len(df)} rows)")
    return df

def gen_demand(n=500):
    np.random.seed(44)
    rows = []
    for _ in range(n):
        day   = np.random.randint(1, 365)
        avg   = np.random.uniform(5, 50)
        usage = max(0, int(avg + np.random.randint(-5, 5)))
        rows.append([day, avg, usage])
    df = pd.DataFrame(rows, columns=['day','avg_usage','actual_usage'])
    df.to_csv(os.path.join(OUT, 'demand_data.csv'), index=False)
    print(f"✅ demand_data.csv ({len(df)} rows)")
    return df

def gen_burnout(n=1000):
    np.random.seed(45)
    rows = []
    for _ in range(n):
        hours    = np.random.uniform(4, 14)
        patients = np.random.randint(5, 30)
        overtime = np.random.randint(0, 20)
        days     = 30
        score = 0
        if hours > 10:    score += 3
        elif hours > 8:   score += 1
        if patients > 20: score += 3
        elif patients > 15: score += 1
        if overtime > 10: score += 3
        elif overtime > 5: score += 1
        risk = 2 if score >= 6 else (1 if score >= 3 else 0)
        rows.append([hours, patients, overtime, days, risk])
    df = pd.DataFrame(rows, columns=['avg_hours','avg_patients','overtime_days','total_days','risk_level'])
    df.to_csv(os.path.join(OUT, 'burnout_data.csv'), index=False)
    print(f"✅ burnout_data.csv ({len(df)} rows)")
    return df

if __name__ == '__main__':
    gen_severity(); gen_discharge(); gen_demand(); gen_burnout()
    print("\n✅ All datasets generated in dataset_generator/")