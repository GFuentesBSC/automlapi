import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY

client_ecs = boto3.client('ecs',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')

def update_flask_service_instances(num_instances):
    num_instances = min(num_instances, 10)
    num_instances = max(num_instances, 0)
    response = client_ecs.update_service(
        cluster='flask-cluster',
        service='predict',
        desiredCount=num_instances
    )
    return response
