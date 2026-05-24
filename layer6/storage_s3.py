import boto3
from botocore.config import Config

s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))

def presign_put_url(key, expires=3600):

    return s3_client.generate_presigned_post(
        Bucket = 'ml-registry-artifacts-dev',
        Key = key,
        ExpiresIn = expires,
            )


def presign_get_url(key, expires=3600):
    
    return s3_client.generate_presigned_url(
            ClientMethod = 'get_object',
            Params={'Bucket': 'ml-registry-artifacts-dev', 'Key': key},
            ExpiresIn = expires

            )
