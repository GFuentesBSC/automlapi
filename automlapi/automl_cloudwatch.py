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

def find_best_period(start_time, end_time):
	max_data_points = 100800
	time_delta = int((end_time-start_time).total_seconds())
	period = time_delta // max_data_points
	period += (60 - period % 60)
	return period

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
	period     = find_best_period(start_time, end_time)

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
	                'Period': period,
	                'Stat': 'Sum',
	                'Unit': 'Count'
	            },
	            'Label': metric_name,
	        },
	    ],
	    StartTime = start_time,
	    EndTime = end_time,
	    ScanBy = 'TimestampAscending'
	)
	try:
		values = response['MetricDataResults'][0]['Values']
		return sum(values)
	except Exception as e:
		print(f"get_production_documents_metric : ERROR : {e}")
		return 0

def get_production_documents_sent(project_id, start_time=None, end_time=None):
	return get_production_documents_metric("Sent", project_id, start_time, end_time)

def get_production_documents_finished(project_id, start_time=None, end_time=None):
	return get_production_documents_metric("Finished", project_id, start_time, end_time)

def get_project_workload(project_id, start_time=None, end_time=None):

	end_time   = (end_time or datetime.now()).replace(second=0, microsecond=0)
	start_time = (start_time or end_time-timedelta(hours=24)).replace(second=0, microsecond=0)
	period     = 60
	response = client_cw.get_metric_data(
	    MetricDataQueries=[
	        {
	            'Id': 'query1',
	            'MetricStat': {
	                'Metric': {
	                    'Namespace': 'Production Orchestrator',
	                    'MetricName': 'received_requests',
	                    'Dimensions': [
	                            {
	                                'Name': 'project_id',
	                                'Value': f"{project_id}"
	                            },
	                        ]
	                },
	                'Period': period,
	                'Stat': 'Sum',
	                'Unit': 'Count'
	            },
	            'Label': 'Requests received',
	        },
	    ],
	    StartTime=start_time,
	    EndTime=end_time,
	    ScanBy='TimestampAscending',
	)
	metric_timestamps 	= [x.strftime("%Y-%m-%d %H:%M:%S") for x in response['MetricDataResults'][0]['Timestamps']]
	metric_values     	= response['MetricDataResults'][0]['Values']
	all_timestamps		= [(start_time + timedelta(seconds=period * i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(int((end_time-start_time).total_seconds()//period))]
	all_values 			= [metric_values[metric_timestamps.index(timestamp)] if timestamp in metric_timestamps else 0 for timestamp in all_timestamps]
	return all_timestamps, all_values

def get_platform_workload(start_time=None, end_time=None):

	end_time   = (end_time or datetime.now()).replace(second=0, microsecond=0)
	start_time = (start_time or end_time-timedelta(hours=24)).replace(second=0, microsecond=0)
	period     = 60

	response = client_cw.get_metric_data(
	    MetricDataQueries=[
	        {
	            'Id': 'query1',
	            'MetricStat': {
	                'Metric': {
	                    'Namespace': 'Production Orchestrator',
	                    'MetricName': 'total_received_requests',
	                },
	                'Period': period,
	                'Stat': 'Sum',
	                'Unit': 'Count'
	            },
	            'Label': 'Requests received',
	        },
	    ],
	    StartTime=start_time,
	    EndTime=end_time,
	    ScanBy='TimestampAscending',
	)
	metric_timestamps 	= [x.strftime("%Y-%m-%d %H:%M:%S") for x in response['MetricDataResults'][0]['Timestamps']]
	metric_values     	= response['MetricDataResults'][0]['Values']
	all_timestamps		= [(start_time + timedelta(seconds=period * i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(int((end_time-start_time).total_seconds()//period))]
	all_values 			= [metric_values[metric_timestamps.index(timestamp)] if timestamp in metric_timestamps else 0 for timestamp in all_timestamps]
	return all_timestamps, all_values
