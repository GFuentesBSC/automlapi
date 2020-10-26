import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY

client_batch = boto3.client('batch',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')

def create_job_definition():
	# REQUIERED PARAMS: jobDefinitionName, type

	'''
	EXAMPLE:

	{
		"jobDefinitionName": "first-run-job-definition",
		"jobDefinitionArn": "arn:aws:batch:us-west-2:749868801319:job-definition/first-run-job-definition:1",
		"revision": 1,
		"status": "ACTIVE",
		"type": "container",
		"parameters": {},
		"containerProperties": {
			"image": "749868801319.dkr.ecr.us-west-2.amazonaws.com/sagemaker-tf-cifar10-example:test_print",
			"vcpus": 1,
			"memory": 2000,
			"command": [],
			"jobRoleArn": "arn:aws:iam::749868801319:role/BasicTrainTaskRole",
			"volumes": [],
			"environment": [],
			"mountPoints": [],
			"ulimits": [],
			"resourceRequirements": []
		},
		"timeout": {
			"attemptDurationSeconds": 100
		}
	}
	'''
	response = client_batch.register_job_definition(
		jobDefinitionName='test-metrics',
		type='container',
		parameters={

		},
		containerProperties= {
			"image": "749868801319.dkr.ecr.us-west-2.amazonaws.com/sagemaker-tf-cifar10-example:test_metrics",
			"vcpus": 1,
			"memory": 2000,
			"command": [],
			"jobRoleArn": "arn:aws:iam::749868801319:role/BasicTrainTaskRole",
			"volumes": [],
			"environment": [],
			"mountPoints": [],
			"ulimits": [],
			"resourceRequirements": []
		},
		timeout={
			'attemptDurationSeconds': 60*60*5
		}
	)

def configure_instance(instance_type, environment):

	try:
		prior = 1 + ['SLOW','NORMAL','FAST'].index(instance_type.upper())
	except ValueError:
		return {'environment': environment}

	resources = []
	if prior > 1:
		resources = [
            {
                'value': f'{(prior-1)*2}', # NORMAL = 2	# FAST = 4
                'type': 'GPU'
            },
        ]

	containerOverrides={
        'vcpus': pow(4, prior),   # SLOW  = 4 		NORMAL = 16		FAST = 64
        'memory': 2048 * prior,   # SLOW  = 2GiB	NORMAL = 4GiB	FAST = 6GiB
        'environment': environment,
        'resourceRequirements': resources
    }
	return containerOverrides

def submit_train_job(params):
	print(f'submit_train_job : INFO : received params = {params}')
	environment = []

	for param in params:
		environment.append({'name': param, 'value': str(params[param])})

	containerOverrides = {'environment': environment}

	response = client_batch.submit_job(
		jobName=str(params['JOB_ID']),
		jobQueue='train-queue',
		jobDefinition=params['TRAINING_IMAGE'],
		parameters={},
		containerOverrides=containerOverrides,
		timeout={
        	'attemptDurationSeconds': params['TIMEOUT']
    	}
	)

	return response

def submit_job(params):
	print(f'submit_job : INFO : received params = {params}')
	environment = []

	for param in params:
		environment.append({'name': param, 'value': str(params[param])})

	containerOverrides = configure_instance(params['INSTANCE_TYPE'], environment)

	response = client_batch.submit_job(
		jobName=str(params['JOB_ID']),
		jobQueue='first-run-job-queue',
		jobDefinition=params['TRAINING_IMAGE'],
		parameters={},
		containerOverrides=containerOverrides,
		timeout={
        	'attemptDurationSeconds': 3600
    	}
	)

	return response

def submit_inf_req(params):
	print("Submit_inf_req - init")
	environment = []

	for param in params:
		environment.append({'name': param, 'value': str(params[param])})

	containerOverrides = configure_instance('Slow', environment)

	response = client_batch.submit_job(
		jobName=str(params['JOB_ID']),
		jobQueue='first-run-job-queue',
		jobDefinition='test-inference',
		parameters={},
		containerOverrides=containerOverrides,
		timeout={
        	'attemptDurationSeconds': 3600
    	}
	)

	return response

def custom_submit(cores):

	response = client_batch.submit_job(
		jobName='CONSOLE',
		jobQueue='first-run-job-queue',
		jobDefinition='test-inference',
		parameters={},
		containerOverrides={
	        'vcpus': cores,   # SLOW  = 4 		NORMAL = 16		FAST = 64
	        'memory': 512,   # SLOW  = 2GiB	NORMAL = 4GiB	FAST = 6GiB
	        'environment': [],
	        'resourceRequirements': []
	    },
		timeout={
        	'attemptDurationSeconds': 3600
    	}
	)

	return response

def launch_pretrain_job(params):

	print(f"launch_pretrain_job : INFO : launching pretrain job ({params['JOB_ID']}) for project ({params['PROJECT_ID']})...")
	environment = []

	for param in params:
		environment.append({'name': param, 'value': str(params[param])})

	# containerOverrides = configure_instance(params['INSTANCE_TYPE'], environment)

	response = client_batch.submit_job(
		jobName=str(params['JOB_ID']),
		jobQueue='pretrain-queue',
		jobDefinition=params['PRETRAIN_IMAGE'],
		parameters={},
		containerOverrides={'environment': environment},
		timeout={
        	'attemptDurationSeconds': 3600 * (1 + int(params['NPAGES'] / 1000))
    	}
	)
	print(f"launch_pretrain_job : INFO : submitted!")
	return response
