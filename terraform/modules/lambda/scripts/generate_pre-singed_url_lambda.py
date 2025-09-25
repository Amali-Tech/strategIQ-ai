import boto3
import os
import json
import uuid
import base64
import hashlib

s3 = boto3.client("s3")
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
    
    # Add metadata to the S3 object
    metadata = {}
    if product_details:
        metadata['product-details'] = product_details
    if product_category:
        metadata['product-category'] = product_category
    if platform:
        metadata['platform'] = platform
    
    presigned_params = {
        "Bucket": BUCKET,
        "Key": object_key,
        "ContentType": filetype
    }
    
    # Add metadata to presigned URL if any exists
    if metadata:
        presigned_params["Metadata"] = metadata
    
    presigned_url = s3.generate_presigned_url(
        "put_object",
        Params=presigned_params,
        ExpiresIn=3600,
    )
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "uploadUrl": presigned_url,
            "imageHash": image_hash,
            "metadata": metadata
        }),
    }