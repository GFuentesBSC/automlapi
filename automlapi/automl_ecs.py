import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, AWS_REGION_NAME
import time
from botocore.exceptions import ClientError
from .automl_elb import (
	get_targets_health,
)

client_ecs = boto3.client('ecs',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name=AWS_REGION_NAME)

def get_servicesArns_of_cluster(cluster_name):
	while True:
		try:
			return client_ecs.list_services(cluster=cluster_name)['serviceArns']
		except ClientError:
			time.sleep(1)
			pass

def get_service(cluster_name, service_name):
	while True:
		try:
			return client_ecs.describe_services(cluster=cluster_name, services=[service_name])['services'][0]
		except ClientError:
			time.sleep(1)
			pass

def get_max_instances(cluster_name, service_name):
	# TODO: IMPLEMENT
	return 5

def update_service_desiredCount(cluster_name, service_name, desiredCount):
	while True:
		try:
			client_ecs.update_service(cluster=cluster_name, service=service_name, desiredCount=desiredCount)
			break
		except ClientError:
			time.sleep(1)
			pass

def drain_instance(cluster_name, instance_id):
	instances_arns = client_ecs.list_container_instances(cluster=cluster_name)['containerInstanceArns']
	container_instances = client_ecs.describe_container_instances(cluster=cluster_name, containerInstances=instances_arns)['containerInstances']
	for container_instance in container_instances:
		if container_instance['ec2InstanceId'] == instance_id:
			container_instance_arn = container_instance['containerInstanceArn']
			client_ecs.update_container_instances_state(cluster=cluster_name, containerInstances=[container_instance_arn], status='DRAINING')
			break

def activate_instance(cluster_name, instance_id):
	instances_arns = client_ecs.list_container_instances(cluster=cluster_name)['containerInstanceArns']
	container_instances = client_ecs.describe_container_instances(cluster=cluster_name, containerInstances=instances_arns)['containerInstances']
	for container_instance in container_instances:
		if container_instance['ec2InstanceId'] == instance_id:
			container_instance_arn = container_instance['containerInstanceArn']
			client_ecs.update_container_instances_state(cluster=cluster_name, containerInstances=[container_instance_arn], status='ACTIVE')
			break

def run_model_deployment(version_id, model_uri):
	response = client_ecs.run_task(
	    launchType='FARGATE',
	    cluster='arn:aws:ecs:eu-west-3:749868801319:cluster/FargateCluster',
		    networkConfiguration={
		        'awsvpcConfiguration': {
		            'subnets': [
		                'subnet-60c56d09',
		            ],
		            'securityGroups': [
		                'sg-ffec8896',
		            ],
		            'assignPublicIp': 'ENABLED'
		        }
		    },
		    overrides={
		        'containerOverrides': [
		            {
		                'name': 'main',
		                'environment': [
		                    {
		                        'name': 'MODEL_URI',
		                        'value': str(model_uri)
		                    },
		                    {
		                        'name': 'VERSION_ID',
		                        'value': str(version_id)
		                    },
		                ],
		            },
		        ],
		    },
		    referenceId='testing-fargate-task-1',
		    taskDefinition='sagemaker_deploy'
		)
	return response['ResponseMetadata']['HTTPStatusCode']

def get_service_instaces_status(cluster, service_name):
	print(f"get_service_instaces_status : INFO : Getting info of service {service_name} (cluster {cluster})...")
	try:
		response = client_ecs.describe_services(cluster=cluster, services=[service_name])
		service = response['services'][0]
		desired = service['desiredCount']
		running = service['runningCount']
		return desired, running
	except:
		return 0, 0

def get_draining_instances_count(cluster_name, service_name):
	try:
		tg_arn = client_ecs.describe_services(cluster=cluster_name, services=[service_name])['services'][0]['loadBalancers'][0]['targetGroupArn']
		targets_health = get_targets_health(tg_arn)
		return len(list(filter(lambda x: x.lower() == 'draining', targets_health)))
	except Exception as e:
		print(f"get_draining_instances_count : ERROR : {e}")
		return 0
