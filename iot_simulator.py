import requests, random, time, sys

BASE  = 'http://localhost:5000'
CREDS = {'email': 'nurse@hospital.com', 'password': 'nurse123'}

def get_token():
    r = requests.post(f'{BASE}/api/auth/login', json=CREDS)
    return r.json().get('token')

def get_patient_ids(token):
    r = requests.get(f'{BASE}/api/patients?status=admitted',
                     headers={'Authorization': f'Bearer {token}'})
    return [p['id'] for p in r.json()]

def push_vitals(token, pid, abnormal=False):
    hr   = random.randint(130, 160) if abnormal else random.randint(60, 100)
    bps  = random.randint(160, 200) if abnormal else random.randint(110, 140)
    bpd  = random.randint(85, 100)  if abnormal else random.randint(70, 85)
    o2   = random.uniform(85, 91)   if abnormal else random.uniform(95, 100)
    temp = random.uniform(39.5, 41) if abnormal else random.uniform(36.5, 37.8)
    r = requests.post(
        f'{BASE}/api/vitals/push/{pid}',
        json={'heart_rate': hr, 'bp_systolic': bps, 'bp_diastolic': bpd,
              'oxygen_level': round(o2,1), 'temperature': round(temp,1)},
        headers={'Authorization': f'Bearer {token}'}
    )
    data = r.json()
    status = '🚨 ALERT' if data.get('alerts') else '✅ Normal'
    print(f"  Patient #{pid}: HR={hr} BP={bps}/{bpd} O2={round(o2,1)} Temp={round(temp,1)} → {status}")

def main():
    print("=" * 50)
    print("  AIHAS IoT Simulator")
    print("=" * 50)
    try:
        token = get_token()
    except Exception:
        print("❌ Cannot connect. Is the server running?")
        sys.exit(1)
    print("✅ Authenticated\n")
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- Cycle {cycle} ({time.strftime('%H:%M:%S')}) ---")
        try:
            pids = get_patient_ids(token)
            if not pids:
                print("No admitted patients found.")
            else:
                for pid in pids[:5]:
                    abnormal = random.random() < 0.2
                    push_vitals(token, pid, abnormal)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(10)

if __name__ == '__main__':
    main()