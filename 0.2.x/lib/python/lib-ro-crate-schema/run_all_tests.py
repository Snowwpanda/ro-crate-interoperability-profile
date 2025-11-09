#!/usr/bin/env python3
"""
Test runner for RO-Crate Schema Library
"""
import sys
import subprocess
from pathlib import Path

def run_test(test_file):
    """Run a single test file and return success status"""
    print(f"\n🧪 Running {test_file.name}")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, str(test_file)], 
                              capture_output=False, 
                              check=True,
                              cwd=test_file.parent)
        print(f"✅ {test_file.name} PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {test_file.name} FAILED (exit code: {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ {test_file.name} ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 RO-Crate Schema Library Test Suite")
    print("=" * 60)
    
    # Find test directory
    test_dir = Path(__file__).parent / "tests"
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return False
    
    # Find all test files
    test_files = list(test_dir.glob("test_*.py"))
    if not test_files:
        print(f"❌ No test files found in {test_dir}")
        return False
    
    print(f"📋 Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    # Run tests
    results = []
    for test_file in test_files:
        success = run_test(test_file)
        results.append((test_file.name, success))
    
    # Summary
    print("\n🎯 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🏆 ALL TESTS PASSED!")
        return True
    else:
        print("💥 SOME TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)