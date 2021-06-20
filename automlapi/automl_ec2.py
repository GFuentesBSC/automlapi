import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, AWS_REGION_NAME

client_ec2 = boto3.client('ec2',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name=AWS_REGION_NAME)

def launch_instances_for_flask(num_instances, cluster_name, template_id, version):
	num_instances = min(num_instances, 20)
	num_instances = max(num_instances, 0)

	# indicate cluster
	userData = f'#!/bin/bash\necho ECS_CLUSTER={cluster_name} >> /etc/ecs/ecs.config\nyum update -y ecs-init\nsystemctl restart docker'

	response = client_ec2.run_instances(
		LaunchTemplate={
			'LaunchTemplateId': template_id,
			'Version': str(version)
		},
		MaxCount=num_instances,
		MinCount=num_instances,
		UserData=userData,
	)

	launched_instances_ids = [x['InstanceId'] for x in response['Instances']]
    return launched_instances_ids
