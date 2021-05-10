import os
import json
from os.path import expanduser

AWS_ACC_KEY_ID = ''
AWS_SEC_ACC_KEY = ''
AWS_REGION_NAME = ''
USER_POOL_ID = ''
CLIENT_ID = ''
CLIENT_SECRET = ''
BD_HOST = ''
BD_PASS = ''
BD_DATABASE = ''
BD_USER = ''
S3_BUCKET = ''

def init():

	try:
		config_file_path = os.environ['AUTOMLAPI_CONFIG_FILE_PATH']
	except Exception as e:
		config_file_path = os.path.join(expanduser("~"),'automlapi.config')

	with open(config_file_path, 'r') as f:
		config_string = f.read()
		j = json.loads(config_string)
		global AWS_ACC_KEY_ID
		AWS_ACC_KEY_ID = j['AWS_ACC_KEY_ID']
		global AWS_SEC_ACC_KEY
		AWS_SEC_ACC_KEY = j['AWS_SEC_ACC_KEY']
		global AWS_REGION_NAME
		AWS_REGION_NAME = j['AWS_REGION_NAME']
		global USER_POOL_ID
		USER_POOL_ID = j['USER_POOL_ID']
		global CLIENT_ID
		CLIENT_ID = j['CLIENT_ID']
		global CLIENT_SECRET
		CLIENT_SECRET = j['CLIENT_SECRET']
		global BD_HOST
		BD_HOST = j['BD_HOST']
		global BD_PASS
		BD_PASS = j['BD_PASS']
		global BD_DATABASE
		BD_DATABASE = j['BD_DATABASE']
		global BD_USER
		BD_USER = j['BD_USER']
		global S3_BUCKET
		S3_BUCKET = j['S3_BUCKET']
