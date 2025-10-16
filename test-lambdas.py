#!/usr/bin/env python3
"""
Test script for Bedrock Agent Lambda functions
This script validates that all Lambda functions can be imported and executed with sample data
"""

import json
import sys
import os
from pathlib import Path

def test_lambda_function(handler_path, test_event=None):
    """Test a single Lambda function"""
    try:
        # Add the handler directory to Python path
        sys.path.insert(0, str(handler_path))
        
        # Import the handler
        import handler
        
        # Create a test event if none provided
        if test_event is None:
            test_event = {
                "parameters": {},
                "inputText": "test input"
            }
        
        # Create a mock context
        class MockContext:
            def __init__(self):
                self.function_name = "test-function"
                self.function_version = "1"
                self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
                self.memory_limit_in_mb = 256
                self.remaining_time_in_millis = lambda: 30000
        
        context = MockContext()
        
        # Call the Lambda handler
        response = handler.lambda_handler(test_event, context)
        
        # Validate response structure
        if not isinstance(response, dict):
            return False, "Response is not a dictionary"
        
        if "messageVersion" not in response:
            return False, "Missing messageVersion in response"
        
        if "response" not in response:
            return False, "Missing response in response"
        
        # Try to parse the response body as JSON
        try:
            response_body = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
            json.loads(response_body)
        except (KeyError, json.JSONDecodeError) as e:
            return False, f"Invalid response body structure: {e}"
        
        return True, "Success"
        
    except Exception as e:
        return False, f"Exception: {e}"
    finally:
        # Clean up sys.path
        if str(handler_path) in sys.path:
            sys.path.remove(str(handler_path))

def main():
    """Main test function"""
    print("🧪 Testing Bedrock Agent Lambda Functions")
    print("=" * 50)
    
    # Find all Lambda function directories
    lambda_dir = Path("lambda")
    if not lambda_dir.exists():
        print("❌ Lambda directory not found")
        return 1
    
    test_results = []
    
    # Test each Lambda function
    for agent_dir in lambda_dir.iterdir():
        if not agent_dir.is_dir() or agent_dir.name == "__pycache__":
            continue
            
        print(f"\n📁 Testing {agent_dir.name} agent functions:")
        
        for function_dir in agent_dir.iterdir():
            if not function_dir.is_dir() or function_dir.name == "__pycache__":
                continue
            
            handler_file = function_dir / "handler.py"
            if not handler_file.exists():
                print(f"  ⚠️  {function_dir.name}: No handler.py found")
                test_results.append((f"{agent_dir.name}/{function_dir.name}", False, "No handler.py"))
                continue
            
            schema_file = function_dir / "schema.json"
            if not schema_file.exists():
                print(f"  ⚠️  {function_dir.name}: No schema.json found")
                test_results.append((f"{agent_dir.name}/{function_dir.name}", False, "No schema.json"))
                continue
            
            # Validate schema.json
            try:
                with open(schema_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                print(f"  ❌ {function_dir.name}: Invalid JSON in schema.json - {e}")
                test_results.append((f"{agent_dir.name}/{function_dir.name}", False, f"Invalid schema.json: {e}"))
                continue
            
            # Test the Lambda function
            success, message = test_lambda_function(function_dir)
            
            if success:
                print(f"  ✅ {function_dir.name}: {message}")
            else:
                print(f"  ❌ {function_dir.name}: {message}")
            
            test_results.append((f"{agent_dir.name}/{function_dir.name}", success, message))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    print(f"  Total functions: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed:")
        for name, success, message in test_results:
            if not success:
                print(f"  • {name}: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main())