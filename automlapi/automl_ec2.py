import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY

client_ec2 = boto3.client('ec2',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')

def launch_instances_for_flask(num_instances):
    num_instances = min(num_instances, 10)
    num_instances = max(num_instances, 0)
    response = client_ec2.run_instances(
        LaunchTemplate={
            'LaunchTemplateId': 'lt-0c52b57123d230c97',
            'Version': '1'
        },
        MaxCount=num_instances,
        MinCount=num_instances
    )
    launched_instances_ids = []
    launched_instances = response['Instances']
    for launched_instance in launched_instances:
        launched_instances_ids.append(launched_instance['InstanceId'])
    print(f"launch_instances_for_flask : INFO : ids launched = {launched_instances_ids}")

    return launched_instances_ids