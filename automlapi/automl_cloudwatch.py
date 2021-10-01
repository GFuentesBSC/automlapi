import boto3
from datetime import datetime, timedelta
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, AWS_REGION_NAME
import json

client_cw = boto3.client('cloudwatch',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name=AWS_REGION_NAME)

def get_client():
	return client_cw

def get_default_initial_time():
	# 1 year ago
	return datetime.now() - timedelta(days=1*365)

def update_production_documents_metric(metric_name, project_id, value):

	response = client_cw.put_metric_data(
	    Namespace="ProductionDocuments",
	    MetricData=[
	        {
	            'MetricName': metric_name,
	            'Dimensions': [
	                {
	                    'Name': "project_id",
	                    'Value': str(project_id)
	                },
	            ],
	            'Timestamp': datetime.now(),
	            'Value': value,
	            'Unit': 'Count',
	            'StorageResolution': 60
	        },
	    ]
	)

	return str(response['ResponseMetadata']['HTTPStatusCode']) == "200"

def get_production_documents_metric(metric_name, project_id, start_time=None, end_time=None):

	start_time = start_time or get_default_initial_time()
	end_time   = end_time   or datetime.now()

	response = client_cw.get_metric_data(
	    MetricDataQueries=[
	        {
	            'Id': 'query_1',
	            'MetricStat': {
	                'Metric': {
	                    'Namespace': "ProductionDocuments",
	                    'MetricName': metric_name,
	                    'Dimensions': [
	                        {
	                            'Name': 'project_id',
	                            'Value': str(project_id)
	                        },
	                    ]
	                },
	                'Period': 60, #The granularity, in seconds, of the returned data points.
	                'Stat': 'Sum',
	                'Unit': 'Count'
	            },
	            'Label': metric_name,
	        },
	    ],
	    StartTime = start_time,
	    EndTime = end_time,
	    ScanBy = 'TimestampAscending',
	    #MaxDatapoints=24*60*60,
	)
	try:
		values = response['MetricDataResults'][0]['Values']
		if len(values) > 1:
			return values[-1] - values[0]
		elif len(values) == 1:
			return values[0]
		else:
			return 0
	except Exception as e:
		print(f"get_production_documents_metric : ERROR : {e}")
		return 0

# def get_production_documents_live_metric(metric_name, project_id):
#
# 	end_time   = datetime.now()
# 	start_time = end_time - timedelta(seconds=120)
#
# 	response = client_cw.get_metric_data(
# 	    MetricDataQueries=[
# 	        {
# 	            'Id': 'query_1',
# 	            'MetricStat': {
# 	                'Metric': {
# 	                    'Namespace': "ProductionDocuments",
# 	                    'MetricName': metric_name,
# 	                    'Dimensions': [
# 	                        {
# 	                            'Name': 'project_id',
# 	                            'Value': str(project_id)
# 	                        },
# 	                    ]
# 	                },
# 	                'Period': 1,
# 	                'Stat': 'Sum',
# 	                'Unit': 'Count'
# 	            },
# 	            'Label': metric_name,
# 	        },
# 	    ],
# 	    StartTime = start_time,
# 	    EndTime = end_time,
# 	    ScanBy = 'TimestampAscending'
# 	)
# 	try:
# 		return response['MetricDataResults'][0]['Values'][-1]
# 	except Exception as e:
# 		print(f"get_production_documents_live_metric : ERROR : {e}")
# 		return 0

def get_production_documents_sent(project_id, start_time=None, end_time=None):
	return get_production_documents_metric("Sent", project_id, start_time, end_time)

def get_production_documents_finished(project_id, start_time=None, end_time=None):
	return get_production_documents_metric("Finished", project_id, start_time, end_time)

# def get_production_documents_inProcess(project_id):
# 	return get_production_documents_live_metric("InProcess", project_id)
#
# def get_production_documents_manual(project_id):
# 	return get_production_documents_live_metric("Manual", project_id)
