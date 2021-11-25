import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, AWS_REGION_NAME

client_batch = boto3.client('batch',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name=AWS_REGION_NAME)

def get_client():
	return client_batch


def start_training(project_id: int,
                   version_id: int,
                   timeout: int = 3600*5):
	"""
	"""
	environment = [
	    {"name": "PROJECT_ID", "value": str(project_id)},
	    {"name": "VERSION_ID", "value": str(version_id)}
	]
	job = client_batch.submit_job(
	    jobName=f"train-pipeline-project_{project_id}-version_{version_id}",
	    jobQueue='train-queue',
	    jobDefinition='train-pipeline-job-definition',
	    containerOverrides={'environment': environment},
	    timeout={'attemptDurationSeconds': timeout}
	)
	return job

def stop_training(version_id: int):
	for status in ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING']:
		jobs = client_batch.list_jobs(jobQueue='train-queue', jobStatus=status)['jobSummaryList']
		if jobs:
			jobs_ids = [job['jobId'] for job in jobs]
			for job_description in client_batch.describe_jobs(jobs=jobs_ids)['jobs']:
			    environment = job_description['container']['environment']
			    for variable in environment:
			        if variable['name'] == "VERSION_ID" and variable['value'] == "55":
			            client_batch.terminate_job(jobId=job_description['jobId'], reason='Training aborted')
