import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY

client_ecs = boto3.client('ecs',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')

def update_flask_service_instances(service, num_instances, cluster_name):
	num_instances = min(num_instances, 20)
	num_instances = max(num_instances, 0)
	print(f"update_flask_service_instances : INFO : Requesting {num_instances} for service {service}...")
	try:
		response = client_ecs.update_service(
			cluster=cluster_name,
			service=service,
			desiredCount=int(num_instances),
			forceNewDeployment=True
		)
	except Exception:
		return False
	return True

def get_service_instaces_status(cluster, service_name):
	print(f"get_service_instaces_status : INFO : Getting info of service {service_name} (cluster {cluster})...")
	response = client_ecs.describe_services(cluster=cluster, services=[service_name])
	try:
		service = response['services'][0]
		desired = service['desiredCount']
		running = service['runningCount']
		return desired, running
	else:
		return 0, 0

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

def create_cluster(cluster_name):
	response = client_ecs.create_cluster(clusterName=cluster_name)

def create_task_definition(task_definition_name, ecr_image):
	response = client_ecs.register_task_definition(
	    family=task_definition_name,
	    taskRoleArn='arn:aws:iam::749868801319:role/ecsTaskExecutionRole',
	    executionRoleArn='arn:aws:iam::749868801319:role/ecsTaskExecutionRole',
	    networkMode='bridge',
	    containerDefinitions=[
	        {
	            'name': 'CONTAINER',
	            'image': ecr_image,
	            'cpu': 0,
	            'memory': 6144,
	            'portMappings': [
	                {
	                    'containerPort': 5000,
	                    'hostPort': 5000,
	                    'protocol': 'tcp'
	                },
	            ],
	            'essential': True,
	            'workingDirectory': '/'
	        },
	    ],
	    requiresCompatibilities=[
	        'EC2',
	    ],
	    cpu='2000',
	    memory='6144'
	)
	if int(response['ResponseMetadata']['HTTPStatusCode']) == 200:
		print(f'create_task_definition : INFO : Created TaskDefinition {task_definition_name}!')
		return str(response['taskDefinition']['taskDefinitionArn'])
	else:
		print(f'create_task_definition : ERROR : Could not create TaskDefinition {task_definition_name}!')
		return False

def create_service(cluster, serviceName, taskDefinition, targetGroupArn):
	response = client_ecs.create_service(
	    cluster=cluster,
	    serviceName=serviceName,
	    taskDefinition=taskDefinition,
	    loadBalancers=[
	        {
	            'targetGroupArn': targetGroupArn,
	            'containerName': 'CONTAINER',
	            'containerPort': 5000
	        },
	    ],
	    desiredCount=0,
	    launchType='EC2',
	    role='arn:aws:iam::749868801319:role/ecsServiceRole',
	    deploymentConfiguration={
	        'maximumPercent': 200,
	        'minimumHealthyPercent': 100
	    },
	    placementStrategy=[
	        {
	            'type': 'binpack',
	            'field': 'memory'
	        },
	    ],
	    healthCheckGracePeriodSeconds=2147483646,
	    schedulingStrategy='REPLICA',
	    enableECSManagedTags=True
	)
	return int(response['ResponseMetadata']['HTTPStatusCode']) == 200
