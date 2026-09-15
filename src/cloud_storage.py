"""
AWS S3 cloud staging layer for raw FX batch rate archives.
"""
import os
import boto3
from botocore.exceptions import ClientError


class AWSS3DataLakeManager:
    """Manages raw exchange rate snapshot syncs to AWS S3 Bronze storage."""

    def __init__(self, bucket_name: str = "ecb-fx-rates-bronze", region: str = "ap-south-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client("s3", region_name=self.region)

    def upload_rates_snapshot(self, local_file: str, s3_key: str) -> bool:
        if not os.path.exists(local_file):
            raise FileNotFoundError(f"Source file not found: {local_file}")
        try:
            self.s3_client.upload_file(local_file, self.bucket_name, s3_key)
            return True
        except ClientError:
            return False
