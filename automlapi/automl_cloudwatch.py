import boto3
from datetime import datetime, timedelta
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY
import json

client_cw = boto3.client('cloudwatch',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')

# usefeul parameters:
day = 86400
hour = 3600
minute = 60

delta_days = 3
start_time = datetime.now() - timedelta(days=delta_days)
end_time = datetime.now()

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

def get_metric_statistics():
	response = client_cw.get_metric_statistics(
		Namespace='AWS/RDS',
		Dimensions=[
			{
				'Name': 'DBInstanceIdentifier',
				'Value': 'aazp6ut01gnv68'
			}
		],
		MetricName='ReadIOPS',
		StartTime=start_time,
		EndTime=end_time,
		Period=hour*2,
		Statistics=[
			'Average'
		]
	)

	# print(str(response).replace('\'', '\"'))
	return response

def get_metrics_rds():
	response = client_cw.get_metric_widget_image(
	MetricWidget= '''{
			"start": "-PT5H",
			"yAxis": {
				"left": {
					"min": 0,
					"max": 700000000
				}
			},
			"metrics": [
				[
					"AWS/RDS",
					"FreeableMemory",
					"DBInstanceIdentifier",
					"aazp6ut01gnv68"
				]
			]
		}'''
	)
	png_text = response['MetricWidgetImage']
	# return io.BytesIO(png_text)
	return png_text

def get_metric_data_rds():
	response = client_cw.get_metric_data(
		MetricDataQueries=[
			{
				'Id':'myId',
				'MetricStat': {
					'Metric': {
						'Namespace':'AWS/RDS',
						'MetricName': 'ReadIOPS',
						'Dimensions': [
							{
								'Name': 'DBInstanceIdentifier',
								'Value': 'aazp6ut01gnv68'
							},
						]
					},
					'Period': hour*2,
					'Stat': 'Average'
				},
			},
		],
		StartTime=start_time,
		EndTime=end_time,
		ScanBy='TimestampAscending',
	)

	# print(str(response).replace('\'', '\"'))
	return response

def get_metric_widget_image_rds():
	metrics = get_metric_data_rds()
	# timestamps = metrics['MetricDataResults'][0]['Timestamps']
	values = metrics['MetricDataResults'][0]['Values']
	content = {
			"start": "-PT"+ str(delta_days*24) +"H",
			"yAxis": {
				"left": {
					"min": min(values)*0.8,
					"max": max(values)*1.2

}			},
			"metrics": [
				[
					"AWS/RDS",
					"ReadIOPS",
					"DBInstanceIdentifier",
					"aazp6ut01gnv68",
					{ "stat": "Average" }
				]
			],
			"period": 60,
			"timezone": "+0100"
		}
	response = client_cw.get_metric_widget_image(
		MetricWidget= json.dumps(content)
	)

	png_text = response['MetricWidgetImage']
	# image = Image.open(io.BytesIO(png_text))
	# image.show()
	return png_text

def get_metric_statistics_s3():
	response = client_cw.get_metric_statistics(
		Namespace='AWS/S3',
		Dimensions=[
			{
				'Name': 'BucketName',
				'Value': 'elasticbeanstalk-us-west-2-749868801319'
			},
			{
				'Name': 'StorageType',
				'Value': 'StandardStorage'
			}
		],
		MetricName='BucketSizeBytes',
		StartTime=start_time,
		EndTime=end_time,
		Period=day,
		Statistics=[
			'Maximum'
		],
		Unit='Bytes'
	)
	# print(str(response).replace('\'', '\"'))
	return response

def get_metric_data_s3():
	response = client_cw.get_metric_data(
		MetricDataQueries=[
			{
				'Id':'myId',
				'MetricStat': {
					'Metric': {
						'Namespace':'AWS/S3',
						'MetricName': 'BucketSizeBytes',
						'Dimensions': [
							{
								'Name': 'BucketName',
								'Value': 'elasticbeanstalk-us-west-2-749868801319'
							},
							{
								'Name': 'StorageType',
								'Value': 'StandardStorage'
							},
						]
					},
					'Period': hour*2,
					'Stat': 'Maximum',
					'Unit': 'Bytes'
				},
			},
		],
		StartTime=start_time,
		EndTime=end_time,
		ScanBy='TimestampAscending',
	)
	# print(str(response).replace('\'', '\"'))
	return response

def get_metric_widget_image_s3():
	metrics = get_metric_data_s3()
	# timestamps = metrics['MetricDataResults'][0]['Timestamps']
	values = metrics['MetricDataResults'][0]['Values']
	content = {
			"start": "-PT"+ str(delta_days*24) +"H",
			"yAxis": {
				"left": {
					"min": min(values)*0.8,
					"max": max(values)*1.2
				}
			},
			"metrics": [
				[
					"AWS/S3",
					"BucketSizeBytes",
					"BucketName",
					"elasticbeanstalk-us-west-2-749868801319",
					"StorageType",
					"StandardStorage"
				]
			],
			"period": 60,
			"timezone": "+0100"
		}
	response = client_cw.get_metric_widget_image(
		MetricWidget= json.dumps(content)
	)
	png_text = response['MetricWidgetImage']
	return png_text

# Para preguntarle al usuario por una fecha concreta, Ejemplo:
# date_entry = input('Enter a date in DD-MM-YYYY format')
# day, month, year = map(int, date_entry.split('-'))
# date1 = datetime.date(year, month, day)
