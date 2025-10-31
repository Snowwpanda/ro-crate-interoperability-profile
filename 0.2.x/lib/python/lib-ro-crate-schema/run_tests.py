#!/usr/bin/env python3
"""
Interactive test runner for RO-Crate bidirectional system
"""

import sys
import subprocess
from pathlib import Path

def run_test(test_file, working_dir=None):
    """Run a test file with proper environment setup"""
    import os
    
    original_dir = Path.cwd()
    
    try:
        if working_dir:
            Path(working_dir).mkdir(parents=True, exist_ok=True)
            os.chdir(working_dir)
        
        # Make test_file relative to the working directory if it's absolute
        if working_dir and test_file.is_absolute():
            try:
                test_file = test_file.relative_to(working_dir)
            except ValueError:
                # If we can't make it relative, use the absolute path
                pass
        
        # Try to use uv if available, otherwise use regular python
        try:
            result = subprocess.run([
                "uv", "run", "python", str(test_file)
            ], check=True, capture_output=False)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to regular python
            result = subprocess.run([
                "python", str(test_file)
            ], check=True, capture_output=False)
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False
    finally:
        os.chdir(original_dir)

def main():
    print("🔬 RO-Crate Bidirectional Test Runner")
    print("=====================================")
    
    # Get the path to test folder
    test_folder = Path(__file__).parent / "tests"
    # Read in the tests dictionary
    if not test_folder.exists():
        print(f"❌ Test folder not found: {test_folder}")
        sys.exit(1)
    tests = {}
    test_counter = 1
    for test in test_folder.glob("test_*.py"):
        test_name = test.stem.replace("test_", "").replace("_", " ").title()
        tests[str(test_counter)] = (test_name, test, None)
        test_counter += 1
    

    
    print("\nAvailable tests:")
    for key, (name, _, _) in tests.items():
        print(f"{key}. {name}")
    print()
    
    choice = input("Select test (number) or press Enter for complete test: ").strip()
    
    if not choice:
        # Run script run_all_tests.py
        script_path = Path(__file__).parent / "run_all_tests.py"
        if script_path.exists():
            print("\n🔄 Running all tests via run_all_tests.py...")
            success = run_test(script_path)
            if success:
                print("\n✅ All tests completed successfully!")
            else:
                print("\n❌ Some tests failed!")
                sys.exit(1)
            print("\n🏁 Test execution completed!")
            return
    
    if choice in tests:
        name, test_file, working_dir = tests[choice]
        print(f"\n🔄 Running {name}...")
        success = run_test(test_file, working_dir)
        
        if success:
            print(f"\n✅ {name} completed successfully!")
        else:
            print(f"\n❌ {name} failed!")
            sys.exit(1)
    else:
        print("❌ Invalid choice. Running default complete test...")
        run_test("test_complete_round_trip.py")
    
    print("\n🏁 Test execution completed!")

if __name__ == "__main__":
    main()