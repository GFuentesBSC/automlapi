import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY

client_ecs = boto3.client('ecs',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')

def update_flask_service_instances(service, num_instances):
    num_instances = min(num_instances, 10)
    num_instances = max(num_instances, 0)
    response = client_ecs.update_service(
        cluster='flask-cluster',
        service=service,
        desiredCount=num_instances
    )
    return response

def services_ready(cluster, service_list):
	response = client_ecs.describe_services(cluster=cluster, services=service_list)
	services = response['services']
	for service in services:
		name    = service['serviceName']
		desired = service['desiredCount']
		running = service['runningCount']
		print(f"services_ready : INFO : Service {name}: Desired = {desired}, Running = {running}")
		if desired != running:
			return False
	return True
