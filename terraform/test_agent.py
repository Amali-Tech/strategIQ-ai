import boto3
import json

def test_bedrock_agent():
    # Initialize the Bedrock Agent Runtime client
    client = boto3.client('bedrock-agent-runtime', region_name='eu-west-1')
    
    try:
        response = client.invoke_agent(
            agentId='4FHLKEL2JE',
            agentAliasId='AV2PECYDKH',
            sessionId='test-session-123',
            inputText='Hi, can you help me analyze a marketing campaign for cultural appropriateness?'
        )
        
        print("✅ Agent invocation successful!")
        print(f"Response: {json.dumps(response, indent=2, default=str)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
if __name__ == "__main__":
    test_bedrock_agent()
