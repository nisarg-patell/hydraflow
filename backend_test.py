import requests
import sys
from datetime import datetime
import json

class WaterReminderAPITester:
    def __init__(self, base_url="https://drink-tracker-61.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=test_headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=test_headers)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_auth_register(self):
        """Test user registration"""
        test_email = f"test_user_{datetime.now().strftime('%H%M%S')}@test.com"
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"email": test_email, "password": "testpass123", "name": "Test User"}
        )
        if success and '_id' in response:
            self.user_id = response['_id']
            print(f"   Registered user ID: {self.user_id}")
        return success

    def test_auth_login_admin(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@waterreminder.com", "password": "admin123"}
        )
        if success and '_id' in response:
            self.user_id = response['_id']
            print(f"   Admin user ID: {self.user_id}")
        return success

    def test_auth_me(self):
        """Test get current user"""
        success, _ = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_auth_logout(self):
        """Test logout"""
        success, _ = self.run_test(
            "Logout",
            "POST",
            "auth/logout",
            200
        )
        return success

    def test_water_log(self):
        """Test water logging"""
        success, response = self.run_test(
            "Log Water Intake",
            "POST",
            "water/log",
            200,
            data={"amount": 250, "label": "Glass"}
        )
        return success

    def test_water_today(self):
        """Test get today's water logs"""
        success, response = self.run_test(
            "Get Today's Water Logs",
            "GET",
            "water/today",
            200
        )
        if success:
            print(f"   Total today: {response.get('total', 0)}ml")
            print(f"   Logs count: {len(response.get('logs', []))}")
        return success

    def test_water_history(self):
        """Test get water history"""
        success, response = self.run_test(
            "Get Water History (7 days)",
            "GET",
            "water/history?days=7",
            200
        )
        if success:
            print(f"   History entries: {len(response.get('history', []))}")
        return success

    def test_settings_get(self):
        """Test get user settings"""
        success, response = self.run_test(
            "Get User Settings",
            "GET",
            "settings",
            200
        )
        if success:
            print(f"   Daily goal: {response.get('daily_goal')}ml")
            print(f"   Theme: {response.get('theme')}")
            print(f"   Reminder interval: {response.get('reminder_interval')} min")
        return success

    def test_settings_update(self):
        """Test update user settings"""
        success, response = self.run_test(
            "Update User Settings",
            "PUT",
            "settings",
            200,
            data={"daily_goal": 2500, "theme": "dark", "reminder_interval": 90}
        )
        if success:
            print(f"   Updated daily goal: {response.get('daily_goal')}ml")
            print(f"   Updated theme: {response.get('theme')}")
        return success

    def test_water_delete_log(self):
        """Test delete water log - first log some water to get a timestamp"""
        # First log some water
        log_success, log_response = self.run_test(
            "Log Water for Delete Test",
            "POST",
            "water/log",
            200,
            data={"amount": 100, "label": "Test Delete"}
        )
        
        if not log_success:
            return False
            
        # Get today's logs to find the timestamp
        today_success, today_response = self.run_test(
            "Get Today's Logs for Delete",
            "GET",
            "water/today",
            200
        )
        
        if not today_success or not today_response.get('logs'):
            return False
            
        # Get the first log's timestamp
        timestamp = today_response['logs'][0]['timestamp']
        
        # Delete the log
        success, _ = self.run_test(
            "Delete Water Log",
            "DELETE",
            f"water/log/{timestamp}",
            200
        )
        return success

def main():
    print("🚰 Water Reminder API Testing")
    print("=" * 50)
    
    tester = WaterReminderAPITester()
    
    # Test sequence
    tests = [
        # Auth tests
        ("Register New User", tester.test_auth_register),
        ("Login as Admin", tester.test_auth_login_admin),
        ("Get Current User", tester.test_auth_me),
        
        # Water logging tests
        ("Log Water Intake", tester.test_water_log),
        ("Get Today's Water", tester.test_water_today),
        ("Get Water History", tester.test_water_history),
        ("Delete Water Log", tester.test_water_delete_log),
        
        # Settings tests
        ("Get Settings", tester.test_settings_get),
        ("Update Settings", tester.test_settings_update),
        
        # Auth cleanup
        ("Logout", tester.test_auth_logout),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for test in failed_tests:
            print(f"   - {test}")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())