import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, AWS_REGION_NAME

client_logs = boto3.client('logs',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name=AWS_REGION_NAME)

def get_client():
	return client_logs
