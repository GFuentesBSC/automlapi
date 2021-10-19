import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, AWS_REGION_NAME
from .automl_ecs import run_model_deployment
from .automl_rds import (
	get_objects_by_conditions as get_object,
	update_object_by_conditions as update_object,
	)
import time
from botocore.exceptions import ClientError

client_sm = boto3.client('sagemaker',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name=AWS_REGION_NAME)

def get_client():
	return client_sm

def deploy_version(version_id, model_uri):
	response = run_model_deployment(version_id, model_uri)
	return str(response) == "200"

def stop_version_deployment(version_id):
	try:
		version = get_object('version', {'id': version_id})[0]
		endpoint_name = version['endpoint']
		endpoint_config_name = client_sm.describe_endpoint(EndpointName=endpoint_name)['EndpointConfigName']
		model_name = client_sm.describe_endpoint_config(EndpointConfigName=endpoint_config_name)['ProductionVariants'][0]['ModelName']
		client_sm.delete_endpoint(EndpointName=endpoint_name)
		client_sm.delete_model(ModelName=model_name)
		update_object('version', {'status': 'COMPLETED', 'endpoint': None}, {'id': version_id})
		return True
	except Exception as e:
		print(f"stop_version_deployment : ERROR : {e}")
		return False
