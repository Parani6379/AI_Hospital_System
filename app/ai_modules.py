import numpy as np, os, joblib

BASE = os.path.join(os.path.dirname(__file__), '..', 'ai_training', 'saved_models')

class SeverityModel:
    def __init__(self):
        try:
            self.model = joblib.load(os.path.join(BASE, 'severity_model.pkl'))
        except:
            self.model = None

    def predict(self, hr, bp, o2, temp, age):
        if self.model:
            try:
                f = np.array([[hr, bp, o2, temp, age]])
                return round(self.model.predict_proba(f)[0][1] * 100, 2)
            except:
                pass
        # Rule-based fallback
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
        try:
            self.model = joblib.load(os.path.join(BASE, 'discharge_model.pkl'))
        except:
            self.model = None

    def predict_days(self, severity, age, diag_code=1):
        if self.model:
            try:
                f = np.array([[severity, age, diag_code]])
                return max(1, int(round(self.model.predict(f)[0])))
            except:
                pass
        if severity >= 75: return 14
        if severity >= 45: return 7
        return 3


class DemandForecaster:
    def __init__(self):
        try:
            self.model = joblib.load(os.path.join(BASE, 'demand_forecast_model.pkl'))
        except:
            self.model = None

    def forecast_7days(self, recent_usage):
        if not recent_usage:
            return [10] * 7
        avg = sum(recent_usage) / len(recent_usage)
        if self.model:
            try:
                f = np.array([[len(recent_usage) + i, avg] for i in range(1, 8)])
                return [max(0, int(p)) for p in self.model.predict(f)]
            except:
                pass
        trend = (recent_usage[-1] - recent_usage[0]) / max(len(recent_usage), 1)
        return [max(0, int(avg + trend * i)) for i in range(1, 8)]


class BurnoutDetector:
    def __init__(self):
        try:
            self.model = joblib.load(os.path.join(BASE, 'burnout_model.pkl'))
        except:
            self.model = None

    def predict_risk(self, avg_hours, avg_patients, overtime_days, total_days=30):
        if self.model:
            try:
                f = np.array([[avg_hours, avg_patients, overtime_days, total_days]])
                idx = int(self.model.predict(f)[0])
                return ['low', 'medium', 'high'][min(idx, 2)]
            except:
                pass
        score = 0
        if avg_hours > 10:    score += 3
        elif avg_hours > 8:   score += 1
        if avg_patients > 20: score += 3
        elif avg_patients > 15: score += 1
        if overtime_days > 10:  score += 3
        elif overtime_days > 5: score += 1
        if score >= 6: return 'high'
        if score >= 3: return 'medium'
        return 'low'


severity_model    = SeverityModel()
discharge_pred    = DischargePredictor()
demand_forecaster = DemandForecaster()
burnout_detector  = BurnoutDetector()