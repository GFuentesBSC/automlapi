import boto3
from datetime import datetime, timedelta
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, AWS_REGION_NAME
import json

client_cw = boto3.client('cloudwatch',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name=AWS_REGION_NAME)

# usefeul parameters:
day = 86400
hour = 3600
minute = 60

delta_days = 3
start_time = datetime.now() - timedelta(days=delta_days)
end_time = datetime.now()

def client_cw():
	return client_cw

def update_metric_info(metricName, metricValue):
	client_cw.put_metric_data(
		MetricData = [
			{
				'MetricName': metricName,
				'Dimensions': [
					{
					'Name': 'Instance name',
					'Value': 'asdsadsd'
					}
				],
				'Unit': 'None',
				'Value': metricValue
			},
		],
		Namespace = 'OpsNamespace'
	)
