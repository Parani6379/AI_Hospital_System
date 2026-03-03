# 🏥 AI Hospital Management System (AIHAS)

An AI-powered hospital management system built with Flask and Python. Uses machine learning models to assist with clinical decisions and hospital operations.

## Features
- Patient registration and management
- Emergency triage with AI severity prediction
- Bed availability tracking
- Pharmacy and medication management
- Appointment scheduling
- Vitals monitoring
- Staff burnout detection
- Demand forecasting and analytics

## AI Models
- **Severity Prediction** — classifies patient emergency severity
- **Discharge Planning** — predicts patient discharge readiness
- **Demand Forecasting** — forecasts hospital resource demand
- **Burnout Detection** — detects staff burnout risk

## Tech Stack
- **Backend:** Python, Flask
- **Authentication:** PyJWT
- **Machine Learning:** scikit-learn, pandas, numpy, joblib
- **Database:** SQLite
- **IoT Simulation:** iot_simulator.py
- **Config:** python-dotenv

## Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate training data
python dataset_generator/generate_all.py

# 3. Train AI models
python ai_training/train_all_models.py

# 4. Seed the database
python seed_database.py

# 5. Copy env file and fill in values
cp .env.example .env

# 6. Run the server
python run.py
```

Visit: http://localhost:5000