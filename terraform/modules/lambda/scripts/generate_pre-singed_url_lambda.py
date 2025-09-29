import boto3
import os
import json
import uuid
import base64
import hashlib

s3 = boto3.client(
    "s3", 
    region_name="eu-west-2",
    config=boto3.session.Config(
        s3={"addressing_style": "virtual"}
    )
)
BUCKET = os.environ.get("BUCKET_NAME")

def generate_image_hash(object_key):
    """Generate the same imageHash that the analysis Lambda creates"""
    return base64.urlsafe_b64encode(hashlib.sha256(object_key.encode()).digest()).decode('utf-8').rstrip('=')


def lambda_handler(event, context):
    body = json.loads(event.get("body","{}"))
    filename = body.get("filename")
    filetype = body.get("filetype")
    product_details = body.get("description", "")
    product_category = body.get("category", "")
    platform = body.get("platform", "")

    print(product_details, product_category, platform)
    
    if not filename or not filetype:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "filename and filetype are required"})
        }
    
    object_key = f"uploads/{uuid.uuid4()}-{filename}"
    image_hash = generate_image_hash(object_key)
    
    # Generate simple presigned URL for PUT request
    presigned_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET,
            "Key": object_key,
            "ContentType": filetype
        },
        ExpiresIn=3600,
    )
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "uploadUrl": presigned_url,
            "imageHash": image_hash
        }),
    }