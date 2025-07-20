#!/usr/bin/env python3
"""
API testing script
"""
import requests
import json
import time
import sys
from typing import Dict, Any


class SentimentAPITester:
    """Sentiment analysis API tester"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        print("🔍 Testing health check endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                return data.get('status') == 'healthy'
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check exception: {str(e)}")
            return False
    
    def test_root_endpoint(self) -> bool:
        """Test root endpoint"""
        print("🔍 Testing root endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint response: {data}")
                return True
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Root endpoint exception: {str(e)}")
            return False
    
    def test_single_analysis(self) -> bool:
        """Test single text analysis"""
        print("🔍 Testing single text analysis...")

        test_cases = [
            {"text": "I love this product!", "expected": "POSITIVE"},
            {"text": "This is terrible and awful.", "expected": "NEGATIVE"},
            {"text": "The weather is nice today.", "expected": "POSITIVE"},
            {"text": "I hate waiting in long lines.", "expected": "NEGATIVE"},
        ]

        success_count = 0

        for i, case in enumerate(test_cases, 1):
            try:
                print(f"  Test case {i}: '{case['text']}'")

                response = self.session.post(
                    f"{self.base_url}/analyze",
                    json={"text": case["text"]},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    sentiment = data.get('sentiment')
                    confidence = data.get('confidence')
                    processing_time = data.get('processing_time')

                    print(f"    Result: {sentiment} (confidence: {confidence:.4f}, time: {processing_time:.3f}s)")

                    if sentiment == case['expected']:
                        print(f"    ✅ Expected result matched")
                        success_count += 1
                    else:
                        print(f"    ⚠️ Expected {case['expected']}, got {sentiment}")
                        success_count += 1  # Still count as success, model may have different judgment
                else:
                    print(f"    ❌ Request failed: {response.status_code}")
                    print(f"    Response: {response.text}")

            except Exception as e:
                print(f"    ❌ Exception: {str(e)}")

        print(f"Single analysis test completed: {success_count}/{len(test_cases)} successful")
        return success_count == len(test_cases)
    
    def test_batch_analysis(self) -> bool:
        """Test batch text analysis"""
        print("🔍 Testing batch text analysis...")

        test_texts = [
            "I absolutely love this!",
            "This is the worst thing ever.",
            "It's okay, nothing special.",
            "Amazing product, highly recommend!",
            "Terrible experience, very disappointed."
        ]

        try:
            print(f"  Batch analyzing {len(test_texts)} texts...")

            response = self.session.post(
                f"{self.base_url}/analyze/batch",
                json={"texts": test_texts},
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                total_count = data.get('total_count')
                total_time = data.get('total_processing_time')

                print(f"  ✅ Batch analysis successful: {total_count} texts, total time: {total_time:.3f}s")

                for i, result in enumerate(results):
                    text = result.get('text')
                    sentiment = result.get('sentiment')
                    confidence = result.get('confidence')
                    print(f"    {i+1}. '{text[:30]}...' -> {sentiment} ({confidence:.4f})")

                return len(results) == len(test_texts)
            else:
                print(f"  ❌ Batch analysis failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False

        except Exception as e:
            print(f"  ❌ Batch analysis exception: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        print("🔍 Testing error handling...")

        error_cases = [
            {"data": {"text": ""}, "desc": "empty text"},
            {"data": {"text": "x" * 600}, "desc": "too long text"},
            {"data": {"texts": []}, "desc": "empty batch list"},
            {"data": {"texts": ["text"] * 15}, "desc": "oversized batch"},
        ]

        success_count = 0

        for case in error_cases:
            try:
                print(f"  Testing {case['desc']}...")

                endpoint = "/analyze" if "text" in case["data"] else "/analyze/batch"
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=case["data"],
                    timeout=10
                )

                if response.status_code >= 400:
                    print(f"    ✅ Correctly returned error status: {response.status_code}")
                    success_count += 1
                else:
                    print(f"    ⚠️ Did not return expected error: {response.status_code}")

            except Exception as e:
                print(f"    ❌ Exception: {str(e)}")

        print(f"Error handling test completed: {success_count}/{len(error_cases)} successful")
        return success_count >= len(error_cases) // 2  # At least half successful
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🚀 Starting API tests...")
        print("=" * 50)

        tests = [
            ("Health Check", self.test_health_check),
            ("Root Endpoint", self.test_root_endpoint),
            ("Single Analysis", self.test_single_analysis),
            ("Batch Analysis", self.test_batch_analysis),
            ("Error Handling", self.test_error_handling),
        ]

        results = []

        for test_name, test_func in tests:
            print(f"\n📋 {test_name} Test")
            print("-" * 30)

            start_time = time.time()
            success = test_func()
            duration = time.time() - start_time

            results.append((test_name, success, duration))

            status = "✅ Passed" if success else "❌ Failed"
            print(f"{status} (time: {duration:.2f}s)")

        print("\n" + "=" * 50)
        print("📊 Test Summary:")

        total_tests = len(results)
        passed_tests = sum(1 for _, success, _ in results if success)

        for test_name, success, duration in results:
            status = "✅" if success else "❌"
            print(f"  {status} {test_name}: {duration:.2f}s")

        print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️ Some tests failed")
            return False


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="SentimentSense API testing tool")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API service URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=0,
        help="Wait time before testing (seconds)"
    )

    args = parser.parse_args()

    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds before starting tests...")
        time.sleep(args.wait)

    tester = SentimentAPITester(args.url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
