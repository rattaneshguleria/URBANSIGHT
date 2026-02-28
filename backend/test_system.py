import requests
import time

print("🌆 Testing UrbanSight System...")
print("="*50)

# Test 1: Dashboard
try:
    r = requests.get("http://localhost:5000")
    print(f"✅ Dashboard: {r.status_code}")
except:
    print("❌ Dashboard: Not accessible")

# Test 2: API
try:
    r = requests.get("http://localhost:5000/api/status")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ API Status: {data.get('status')}")
        print(f"   Analyses: {data.get('analyses_count')}")
        print(f"   Alerts: {data.get('alerts_count')}")
except:
    print("❌ API: Not responding")

# Test 3: Demo Analysis
try:
    r = requests.post("http://localhost:5000/api/demo/analyze")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ Demo Analysis: Success")
        print(f"   Alerts: {len(data.get('alerts', []))}")
except:
    print("❌ Demo Analysis: Failed")

print("="*50)
print("\n📱 Open http://localhost:5000 in your browser")