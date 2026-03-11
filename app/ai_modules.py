import os, joblib

BASE = os.path.join(os.path.dirname(__file__), '..', 'ai_training', 'saved_models')

def _load(name):
    try:
        return joblib.load(os.path.join(BASE, name))
    except Exception:
        return None


class SeverityModel:
    def __init__(self):
        self.model = _load('severity_model.pkl')

    def predict(self, hr, bp, o2, temp, age):
        if self.model:
            try:
                features = [[float(hr), float(bp), float(o2), float(temp), float(age)]]
                return round(float(self.model.predict_proba(features)[0][1]) * 100, 2)
            except Exception:
                pass
        # Rule-based fallback (no numpy needed)
        score = 0
        if hr > 120 or hr < 45:  score += 30
        elif hr > 100:            score += 15
        if o2 < 90:               score += 35
        elif o2 < 94:             score += 20
        if bp > 170:              score += 20
        elif bp > 150:            score += 10
        if temp > 39.5:           score += 15
        elif temp > 38.5:         score += 8
        if age > 70:              score += 10
        return min(round(score, 2), 100)

    def classify(self, score):
        if score >= 75: return 'critical'
        if score >= 45: return 'moderate'
        return 'stable'


class DischargePredictor:
    def __init__(self):
        self.model = _load('discharge_model.pkl')

    def predict_days(self, severity, age, diag_code=1):
        if self.model:
            try:
                features = [[float(severity), float(age), float(diag_code)]]
                return max(1, int(round(float(self.model.predict(features)[0]))))
            except Exception:
                pass
        if severity >= 75: return 14
        if severity >= 45: return 7
        return 3


class DemandForecaster:
    def __init__(self):
        self.model = _load('demand_forecast_model.pkl')

    def forecast_7days(self, recent_usage):
        if not recent_usage:
            return [10] * 7
        avg = sum(recent_usage) / len(recent_usage)
        if self.model:
            try:
                features = [[len(recent_usage) + i, avg] for i in range(1, 8)]
                preds = self.model.predict(features)
                return [max(0, int(p)) for p in preds]
            except Exception:
                pass
        trend = (recent_usage[-1] - recent_usage[0]) / max(len(recent_usage), 1)
        return [max(0, int(avg + trend * i)) for i in range(1, 8)]


class BurnoutDetector:
    def __init__(self):
        self.model = _load('burnout_model.pkl')

    def predict_risk(self, avg_hours, avg_patients, overtime_days, total_days=30):
        if self.model:
            try:
                features = [[float(avg_hours), float(avg_patients), float(overtime_days), float(total_days)]]
                idx = int(self.model.predict(features)[0])
                return ['low', 'medium', 'high'][min(idx, 2)]
            except Exception:
                pass
        score = 0
        if avg_hours > 10:       score += 3
        elif avg_hours > 8:      score += 1
        if avg_patients > 20:    score += 3
        elif avg_patients > 15:  score += 1
        if overtime_days > 10:   score += 3
        elif overtime_days > 5:  score += 1
        if score >= 6: return 'high'
        if score >= 3: return 'medium'
        return 'low'


severity_model    = SeverityModel()
discharge_pred    = DischargePredictor()
demand_forecaster = DemandForecaster()
burnout_detector  = BurnoutDetector()