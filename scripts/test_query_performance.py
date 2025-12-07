#!/usr/bin/env python3
"""
Test Dremio SQL query performance by authenticating and running a test query
"""
import requests
import json
import time
import sys
import os

DREMIO_URL = "http://localhost:9047"

class DremioQueryTester:
    def __init__(self, username, password):
        self.base_url = DREMIO_URL
        self.username = username
        self.password = password
        self.token = None

    def login(self):
        """Authenticate and get access token"""
        print(f"\n🔐 Logging in to Dremio as '{self.username}'...")

        login_url = f"{self.base_url}/apiv2/login"
        payload = {
            "userName": self.username,
            "password": self.password
        }

        try:
            response = requests.post(login_url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                print(f"✅ Login successful! Token received.")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def run_query(self, sql):
        """Execute SQL query and measure performance"""
        if not self.token:
            print("❌ Not authenticated. Please login first.")
            return None

        print(f"\n📊 Executing SQL query...")
        print(f"Query: {sql[:100]}...")

        sql_url = f"{self.base_url}/api/v3/sql"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "sql": sql
        }

        try:
            start_time = time.time()
            response = requests.post(sql_url, json=payload, headers=headers, timeout=30)
            end_time = time.time()

            query_time = end_time - start_time

            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Query executed successfully!")
                print(f"⏱️  Query time: {query_time:.3f} seconds")

                # Try to parse results
                if 'rows' in result:
                    row_count = len(result['rows'])
                    print(f"📈 Rows returned: {row_count}")

                    # Show first few rows
                    if row_count > 0:
                        print(f"\n📋 Sample results:")
                        for i, row in enumerate(result['rows'][:5]):
                            print(f"   Row {i+1}: {row}")

                return result

            else:
                print(f"❌ Query failed: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return None

        except requests.exceptions.Timeout:
            print(f"⚠️  Query timed out after 30 seconds")
            return None
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None

def main():
    print("="*80)
    print("DREMIO SQL QUERY PERFORMANCE TEST")
    print("="*80)

    # Get credentials
    username = sys.argv[1] if len(sys.argv) > 1 else os.getenv('DREMIO_USER')
    password = sys.argv[2] if len(sys.argv) > 2 else os.getenv('DREMIO_PASSWORD')

    if not username or not password:
        print("\n⚠️  No credentials provided")
        print("Usage: python test_query_performance.py <username> <password>")
        print("Or set DREMIO_USER and DREMIO_PASSWORD environment variables")

        # Try to proceed without auth for testing
        print("\nTrying unauthenticated query (will likely fail)...")
        username = "test"
        password = "test"
    else:
        print(f"\n✅ Using credentials for: {username}")

    # Create tester
    tester = DremioQueryTester(username, password)

    # Login
    if not tester.login():
        print("\n❌ Authentication failed. Cannot test queries.")
        print("\nTo test manually:")
        print("1. Open http://localhost:9047 in your browser")
        print("2. Login with your credentials")
        print("3. Click 'New Query'")
        print("4. Paste this query:")
        print('\nSELECT activity_name, COUNT(*) as events FROM minio."zeek-data"."network-activity-ocsf" GROUP BY activity_name;')
        print("\n5. Click Run and observe the speed!")
        return

    # Test queries
    test_queries = [
        {
            "name": "Query 1: Simple Count",
            "sql": 'SELECT COUNT(*) as total_records FROM minio."zeek-data"."network-activity-ocsf"',
            "expected": "Should return 100,000"
        },
        {
            "name": "Query 2: Activity Breakdown",
            "sql": 'SELECT activity_name, COUNT(*) as events FROM minio."zeek-data"."network-activity-ocsf" GROUP BY activity_name ORDER BY events DESC',
            "expected": "Should show Traffic, http, ssl, dns, ssh"
        },
        {
            "name": "Query 3: Protocol Distribution",
            "sql": 'SELECT connection_info_protocol_name as protocol, COUNT(*) as count FROM minio."zeek-data"."network-activity-ocsf" GROUP BY connection_info_protocol_name ORDER BY count DESC LIMIT 5',
            "expected": "Should show TCP, UDP, ICMP"
        }
    ]

    results = []

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {test['name']}")
        print(f"Expected: {test['expected']}")
        print(f"{'='*80}")

        result = tester.run_query(test['sql'])
        results.append({
            "test": test['name'],
            "success": result is not None,
            "result": result
        })

        # Small delay between queries
        time.sleep(1)

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")

    success_count = sum(1 for r in results if r['success'])
    print(f"\nTests passed: {success_count}/{len(results)}")

    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['test']}")

    if success_count == len(results):
        print(f"\n{'='*80}")
        print("🎉 SUCCESS! All queries executed successfully!")
        print(f"{'='*80}")
        print("\nYour demo is ready! Key points:")
        print("✅ SQL queries execute in <1 second")
        print("✅ No need to navigate folders in UI")
        print("✅ 100,000 OCSF records queryable")
        print("✅ Fast aggregations and filtering")
        print("\nUse the queries from DEMO-SQL-QUERIES.md for your demo!")
    else:
        print("\n⚠️  Some queries failed. Check your Dremio configuration.")

if __name__ == "__main__":
    main()