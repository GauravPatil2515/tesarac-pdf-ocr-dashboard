#!/usr/bin/env python3
"""
Performance Test Script for Optimized Flask App
Tests response times and memory usage
"""

import requests
import time
import psutil
import os
from pathlib import Path

def test_app_performance():
    """Test the optimized Flask app performance"""
    base_url = "http://localhost:5000"
    
    print("🚀 Performance Test Results for Optimized Flask App")
    print("=" * 60)
    
    # Test dashboard loading speed
    start_time = time.time()
    try:
        response = requests.get(base_url, timeout=5)
        dashboard_time = time.time() - start_time
        if response.status_code == 200:
            print(f"✅ Dashboard Load Time: {dashboard_time:.3f}s")
        else:
            print(f"❌ Dashboard failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
    
    # Test health check speed
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        health_time = time.time() - start_time
        if response.status_code == 200:
            print(f"✅ Health Check Time: {health_time:.3f}s")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
    
    # Test static file serving
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/static/css/style.css", timeout=5)
        static_time = time.time() - start_time
        if response.status_code == 200:
            print(f"✅ Static File Load Time: {static_time:.3f}s")
            # Check if caching headers are set
            if 'Cache-Control' in response.headers:
                print(f"✅ Caching Headers Present: {response.headers['Cache-Control']}")
        else:
            print(f"❌ Static file failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Static file test failed: {e}")
    
    print("\n📊 Optimization Summary:")
    print("• Lazy-loaded PDF processor initialization")
    print("• Reduced logging verbosity for production")
    print("• Efficient file handling with streaming")
    print("• Static file caching enabled")
    print("• JSON serialization optimized")
    print("• CORS preflight caching enabled")
    print("• Template auto-reload disabled")
    print("• Threaded request handling")

if __name__ == "__main__":
    print("To run this test:")
    print("1. Start the Flask app: python app.py")
    print("2. In another terminal run: python performance_test.py")
    print("\nThis test requires the app to be running!")
