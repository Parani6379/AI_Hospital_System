# 🏥 AI Hospital Management System (AIHAS)

An advanced, AI-powered hospital management system built with Flask and Python. AIHAS integrates machine learning models to assist medical professionals with clinical decisions, automate hospital operations, and improve overall patient care and resource management.

---

## 🌟 Core Features

- **Patient Management & EMR**: Complete electronic medical records tracking, complete with patient history and real-time medical updates.
- **Emergency Triage & AI Severity**: Automatically classifies patient emergency severity (Critical, Moderate, Stable) based on vitals and age.
- **Vitals Monitoring (IoT Simulator)**: Real-time simulation of patient vitals with integrated anomaly detection that instantly alerts staff of abnormal readings.
- **Bed & Ward Management**: Real-time tracking of ward capacity and individual bed availability.
- **Pharmacy & Inventory Control**: Track medication stocks, dispense medications safely to patients, and trigger low-stock alerts automatically.
- **Appointment Scheduling**: Doctors can manage their availability while patients or staff can fluently book consultations.
- **Predictive Analytics Dashboard**: Demand forecasting that plans hospital resource requirements over a 7-day period based on historical usage.
- **Staff Burnout Detection**: Analyzes work hours, patient load, and overtime frequency to proactively assess staff burnout risk (Low, Medium, High).
- **Discharge Planning**: AI model predicts the optimal number of days until a patient's safe discharge, allowing the hospital to streamline bed turnover.

---

## 🧠 Integrated AI Models

AIHAS leverages scikit-learn to deploy several powerful predictive models:
1. **Severity Prediction Model** — Classifies patient emergency severity score and condition via vitals and age points.
2. **Discharge Planning Model** — Predicts patient discharge readiness and stay duration.
3. **Demand Forecasting Model** — Forecasts hospital resource demands, ensuring adequate staffing and supplies.
4. **Burnout Detection Model** — Evaluates work metrics (hours, patients seen, overtime) to flag high burnout risks among the hospital workforce.

---

## 🛠 Tech Stack

- **Backend Framework:** Python, Flask, Werkzeug
- **Template Engine:** Jinja2
- **Authentication:** PyJWT (Custom Token-based Auth)
- **Machine Learning Data Processing:** scikit-learn, pandas, numpy, joblib
- **Database:** SQLite (via standard Python sqlite3)
- **Environment & Config:** python-dotenv
- **Real-Time Data Injection:** Built-in `iot_simulator.py`

---

## ⚙️ Setup & Installation

Follow these steps to get the AIHAS project up and running locally.

```bash
# 1. Clone the repository and navigate to the project directory
cd aihas

# 2. Create and activate a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Configure Environment Variables
cp .env.example .env
# Edit .env to add your necessary keys (like JWT_SECRET)

# 5. Generate mock training data
python dataset_generator/generate_all.py

# 6. Train all AI models
python ai_training/train_all_models.py

# 7. Initialize and seed the SQLite database
python seed_database.py

# 8. Start the Flask server
python run.py
```

### 📡 Running the IoT Simulator

In a separate terminal, while the Flask server is running, you can start the IoT vitals simulator to generate real-time patient metric updates:
```bash
python iot_simulator.py
```

---

## 🌐 Access the Application

Once everything is running, visit the web interface at:  
**http://localhost:5000**