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
        print(f"Session ID: {response['sessionId']}")
        
        # Read the streaming response
        event_stream = response['completion']
        full_response = ""
        
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_data = json.loads(chunk['bytes'].decode())
                    if 'type' in chunk_data and chunk_data['type'] == 'chunk':
                        if 'bytes' in chunk_data:
                            text = chunk_data['bytes'].decode()
                            full_response += text
                            print(text, end='', flush=True)
        
        print(f"\n\n📝 Full Response: {full_response}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    test_bedrock_agent()
