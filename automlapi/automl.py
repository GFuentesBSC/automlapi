import os
import json

config_file_path = (os.environ.get('AUTOMLAPI_CONFIG_FILE_PATH') or
                    os.path.join(os.path.expanduser("~"), 'automlapi.config'))
CONFIG = json.load(open(config_file_path, 'r'))


AWS_ACC_KEY_ID = CONFIG.get('AWS_ACC_KEY_ID')
AWS_SEC_ACC_KEY = CONFIG.get('AWS_SEC_ACC_KEY')
AWS_REGION_NAME = CONFIG.get('AWS_REGION_NAME')
USER_POOL_ID = CONFIG.get('USER_POOL_ID')
CLIENT_ID = CONFIG.get('CLIENT_ID')
CLIENT_SECRET = CONFIG.get('CLIENT_SECRET')
BD_HOST = CONFIG.get('BD_HOST')
BD_PASS = CONFIG.get('BD_PASS')
BD_DATABASE = CONFIG.get('BD_DATABASE')
BD_USER = CONFIG.get('BD_USER')
