# import MySQLdb as mysql
import pymysql as mysql
import os
import hashlib
import json
from .automl import BD_HOST, BD_PASS, BD_DATABASE, BD_USER

def hash_password(password):
    n = 100000
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', n).hex()
    return hashed_password

def run_exists(query):

    exists = False

    try:
        db = mysql.connect(host=BD_HOST,
                database=BD_DATABASE,
                user=BD_USER,
                password=BD_PASS)
        cursor = db.cursor()
        cursor.execute(query)
        response = cursor.fetchall()
        exists = len(response) > 0
    except Exception as e:
        print(f"run_exists - ERROR - {e}")
    finally:
        db.close()

    return exists

def run_select(query):
    result = []

    try:
        db = mysql.connect(host=BD_HOST,
                database=BD_DATABASE,
                user=BD_USER,
                password=BD_PASS)
        cursor = db.cursor()
        cursor.execute(query)
        response = cursor.fetchall()
        field_names = [i[0] for i in cursor.description]
        for elem in response:
            result.append({})
            for index, value in enumerate(elem):
                result[-1][field_names[index]] = value
    except Exception as e:
        print(f"run_select - ERROR - {e}")
    finally:
        db.close()
    return result

def run_insert(query):
	pk = -1
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		cursor = db.cursor()
		cursor.execute(query)
		pk = cursor.lastrowid
		db.commit()
	except mysql.IntegrityError:
		pass
	except Exception as e:
		print(f"run_insert : ERROR :  {e}")
	finally:
		db.close()
	return pk

def run_update(query):
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)

		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
	except Exception as e:
		print("run_update - ERROR " + str(e))
	finally:
		db.close()

def run_multiple_insert(queries):
    pks = []
    try:
        db = mysql.connect(host=BD_HOST,
                            database=BD_DATABASE,
                            user=BD_USER,
                            password=BD_PASS)
        cursor = db.cursor()
        for query in queries:
            cursor.execute(query)
            pks.append(cursor.lastrowid)
        db.commit()
    except Exception as e:
        print(f"run_multiple_insert : ERROR :  {e}")
    finally:
        db.close()
    return pks

def insert_n_objects(objectName, objects):

    table_name = f'neuralplatform_{objectName.lower()}'
    queries = []
    for object in objects:
        fields = ""
        values = ""
        for key in object:
            fields += key + ', '
            value = object[key]
            if isinstance(value, str):
                value = '"' + value + '"'
            values += str(value) + ', '
        else:
            fields = fields[:-2]
            values = values[:-2]
        queries.append(f'INSERT INTO {table_name}({fields}) VALUES({values});')

    return run_multiple_insert(queries)

def get_n_objects_by_key(objectName, n=1, key='id', keyValue=1):

    operator = '='
    if isinstance(keyValue, list):
        operator = 'IN'
        keyValue = '(' + str(keyValue)[1:-1] + ')'
    elif isinstance(keyValue, str):
        keyValue = '"' + keyValue + '"'
    query = f'SELECT * FROM neuralplatform_{objectName.lower()} WHERE {key} {operator} {keyValue};'
    elements = run_select(query)
    if len(elements) > 0:
        return elements[:n]
    return None

def update_object_by_key(objectName, key='id', keyValue=1, fields=None):

    if fields:
        operator = '='
        if isinstance(keyValue, list):
            operator = 'IN'
            keyValue = '(' + str(keyValue)[1:-1] + ')'
        elif isinstance(keyValue, str):
            keyValue = '"' + keyValue + '"'
        changes = ""
        for field in fields:
            value = fields[field]
            if isinstance(value, str):
                value = '"' + value + '"'
            changes += field + ' = ' + str(value) + ', '
        else:
            changes = changes[:-2]
        query = f'UPDATE neuralplatform_{objectName.lower()} SET {changes} WHERE {key} {operator} {keyValue};'
        run_update(query)

def get_projects_of_projectManager(projectManager_id):
	query = f"SELECT project_id FROM neuralplatform_projectmanagerassignedproject WHERE projectManager_id = {projectManager_id};"
	project_ids = run_select(query)
	return project_ids

def get_bucketName_by_page_id(page_id):
    try:
        query = "SELECT s3Bucket FROM neuralplatform_account WHERE id = " + \
            "(SELECT account_id FROM neuralplatform_project WHERE id = " + \
            "(SELECT project_id FROM neuralplatform_dataset WHERE id = " + \
            "(SELECT dataset_id FROM neuralplatform_document WHERE id = " + \
            f"(SELECT document_id FROM neuralplatform_page WHERE id = {page_id}))));"
        return run_select(query)[0]
    except Exception as e:
        print(f"get_bucketName_by_page_id : Error : {e}")
        return ""


def validate_projectManager(account_code, username, hashed_password):
    accounts = get_n_objects_by_key('account', 1, 'code', account_code)
    if accounts:
        account_id = int(accounts[0]['id'])
        projectManagers = get_n_objects_by_key('projectmanager', None, 'account_id', account_id)
        if projectManagers:
            for pm in projectManagers:
                if pm['username'] == username and pm['password'] == hashed_password:
                    return True
    return False

def validate_admin(account_code, username, hashed_password):
    accounts = get_n_objects_by_key('account', 1, 'code', account_code)
    if accounts:
        account = accounts[0]
        return account['username'] == username and account['password'] == hashed_password
    return False

def validate_user(account_code, username, password):
    hashed_password = hash_password(password)
    return validate_admin(account_code, username, hashed_password) or validate_projectManager(account_code, username, hashed_password)

def insert_document(uploadDate, filename, extension, phase, uri, nPages, tagged, training, dataset_id, uploadMethod_id):
	query = f'INSERT INTO neuralplatform_document(uploadDate, name, extension, phase, uri, nPages, tagged, training, dataset_id, uploadMethod_id) ' + \
			f'VALUES ("{uploadDate}", "{filename}", "{extension}", "{phase}", "{uri}", {nPages}, {tagged}, {training}, {dataset_id}, {uploadMethod_id});'
	return run_insert(query)

def insert_request(phase, requestDate, document_id, project_id):
	query = f'INSERT INTO neuralplatform_request(phase, requestDate, document_id, project_id) ' + \
			f'VALUES ("{phase}", "{requestDate}", {document_id}, {project_id});'
	return run_insert(query)

def insert_page(imgUri, ocrUri, document_id):
    query = f'INSERT INTO neuralplatform_page(imgUri, ocrUri, document_id) ' + \
            f'VALUES ("{imgUri}", "{ocrUri}", {document_id});'
    return run_insert(query)

def get_pending_and_unblocked_steps():
    query1 = 'SELECT * FROM neuralplatform_step WHERE status = "pending";'
    pending_steps = run_select(query1)
    unblocked_steps = []
    if len(pending_steps) > 0:
        pending_stepDefinitions = list(set([x['stepDefinition_id'] for x in pending_steps]))
        unblocked_stepDefinitions = []
        query2 = 'SELECT id, blockingStep_id FROM neuralplatform_stepdefinition;'
        stepDefinitions = run_select(query2)
        dependencies = {s['id']: s['blockingStep_id'] for s in stepDefinitions}
        for pending_stepDefinition in pending_stepDefinitions:
            sd_dependency = dependencies[pending_stepDefinition] or -1
            if not run_exists(f'SELECT id FROM neuralplatform_step WHERE status NOT IN ("succeeded", "error") AND stepDefinition_id = {sd_dependency}'):
                unblocked_stepDefinitions.append(pending_stepDefinition)
        unblocked_steps = list(filter(lambda x: x['stepDefinition_id'] in unblocked_stepDefinitions, pending_steps))
    return unblocked_steps

######## DEPRECATED ########

def get_user_pk_by_username(username):
	query = f"SELECT id FROM automlapp_user WHERE username = '{username}';"
	pk = run_select(query)[0]
	return pk

def get_user_pk_by_username_password(username, password):
	pk = -1
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = "SELECT id FROM automlapp_user WHERE username = \"" + username + "\" AND password = \"" + password + "\""
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		pk = response[0]
	except:
		print("get_user_pk_by_username_password - ERROR")
	finally:
		db.close()
	return pk

def get_project_pk_by_user_pk_project_name(user_pk, project_name):
	pk = -1
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT id FROM automlapp_project WHERE user_id = {user_pk} AND proj_name = "{project_name}";'
		# query = "SELECT id FROM automlapp_project WHERE user_id = " + str(user_pk) + " AND proj_name = \"" + project_name + "\";"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		pk = response[0]
	except Exception as e:
		print("get_project_pk_by_user_pk_project_name - ERROR " + str(e))
	finally:
		db.close()
	return pk

def get_project_id_by_model_id(model_id):
	project_id = -1
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT project_id FROM automlapp_modelversion WHERE id = {model_id};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response[0] != None:
			project_id = int(response[0])
	except Exception as e:
		print("get_project_id_by_model_id - ERROR " + str(e))
	finally:
		db.close()
	return project_id

def get_project_name_by_project_pk(project_pk):
	name = ""
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT proj_name FROM automlapp_project WHERE id = {project_pk};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		name = str(response[0])
	except Exception as e:
		print("get_project_name_by_project_pk : ERROR : " + str(e))
	finally:
		db.close()
	return name

def get_document_count_by_project_id_and_label(project_id, label):
	count = 0
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT COUNT(*) FROM automlapp_file WHERE project_id = {project_id} AND label = {label};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		count = int(response[0])
	except Exception as e:
		print("get_document_count_by_project_id_and_label : ERROR : " + str(e))
	finally:
		db.close()
	return count

def insert_files_to_rds(paths, project_name, user_pk):
	inserted = False
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		project_pk = get_project_pk_by_user_pk_project_name(user_pk, project_name)
		cursor = db.cursor()

		for file_path in paths:
			file_name, file_ext = os.path.splitext(os.path.basename(file_path))
			file_ext = file_ext.replace('.','')
			query = '''INSERT INTO automlapp_file(file_type, file_name, tag_manual, uri, project_id, trained)
								VALUES("{}","{}",{},"{}",{},{})'''.format(file_ext, file_name, 0, file_path, project_pk, 0)
			cursor.execute(query)
			print(f"inserted file {file_path} to RDS")
		db.commit()
	except mysql.IntegrityError:
		pass
	except Exception as e:
		print("insert_file - ERROR " + str(e))
	finally:
		db.close()
	return True

def update_job_result(job_id, result):
	result = round(result, 2)
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)

		query = f'UPDATE automlapp_job SET result = {result} where id = {job_id};'
		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
	except Exception as e:
		print("update_job_result - ERROR " + str(e))
	finally:
		db.close()

def get_png_uri_from_page_id(page_id):
	uri = None
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT png_uri FROM automlapp_page WHERE id = {page_id};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		uri = response[0]
	except Exception as e:
		print("get_png_uri_from_page_id - ERROR " + str(e))
	finally:
		db.close()
	return uri

def get_file_uri_and_label_from_id(file_id):
	uri = label = None
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT uri, label FROM automlapp_file WHERE id = {file_id};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		uri = response[0]
		label = response[1]
	except Exception as e:
		print("get_file_uri_from_id : ERROR : " + str(e))
	finally:
		db.close()
	return uri, label

def get_trained_model_path(project_id):
	path = None
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT trained_model_path FROM automlapp_model WHERE project_id = {project_id};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		path = response[0]
	except Exception as e:
		print("get_trained_model_path : ERROR : " + str(e))
	finally:
		db.close()
	return path

def get_npages_to_preprocess_for_project(project_id):
	npages = 0
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT SUM(npages) FROM automlapp_file WHERE project_id = {project_id} AND trained = 0 AND preprocessed = 0;'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response[0] != None:
			npages = response[0]
	except Exception as e:
		print("get_npages_to_preprocess_for_project : ERROR : " + str(e))
	finally:
		db.close()
	return int(npages)

def get_npages_of_file(file_id):
	npages = 0
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT npages FROM automlapp_file WHERE id = {file_id};'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response[0] != None:
			npages = response[0]
	except Exception as e:
		print("get_npages_of_file : ERROR : " + str(e))
	finally:
		db.close()
	return int(npages)

def all_pages_processed_for_file_ids(file_ids):
	all_processed = False
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query1 = f'SELECT SUM(npages) FROM automlapp_file WHERE id IN ({str(file_ids)[1:-1]});'
		query2 = f'SELECT COUNT(*) FROM automlapp_page WHERE file_id IN ({str(file_ids)[1:-1]}) AND ocr_uri IS NOT NULL;'
		cursor = db.cursor()
		cursor.execute(query1)
		result1 = cursor.fetchone()[0]
		if result1:
			total_pages = int(result1)
			cursor.execute(query2)
			result2 = cursor.fetchone()[0]
			if result2:
				processed_pages = int(result2)
				all_processed = total_pages == processed_pages
	except Exception as e:
		print("all_pages_processed_for_file_ids : ERROR : " + str(e))
	finally:
		db.close()
	return all_processed

def set_files_preprocessed(file_ids):
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'UPDATE automlapp_file SET preprocessed = 1 WHERE id IN ({str(file_ids)[1:-1]});'
		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
	except Exception as e:
		print("set_files_preprocessed : ERROR : " + str(e))
	finally:
		db.close()

def get_file_ids_to_preprocess_for_project(project_id):
	ids = []
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT id FROM automlapp_file WHERE project_id = {project_id} AND trained = 0 AND preprocessed = 0;'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchall()
		for row in response:
			ids.append(row[0])
	except Exception as e:
		print("get_file_ids_to_preprocess_for_project : ERROR : " + str(e))
	finally:
		db.close()
	return ids

def get_file_ids_completely_processed_for_project(project_id):
	ids = []
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT DISTINCT file_id FROM automlapp_page pg WHERE file_id IN (SELECT id FROM automlapp_file WHERE project_id = {project_id}) AND NOT EXISTS (SELECT * FROM automlapp_page pg2 WHERE pg.file_id = pg2.file_id AND ocr_uri IS null);'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchall()
		for row in response:
			ids.append(row[0])
	except Exception as e:
		print("get_file_ids_completely_processed_for_project : ERROR : " + str(e))
	finally:
		db.close()
	return ids

def get_pages_of_files(file_ids):
	ids = []
	png_uris = []
	ocr_uris = []
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT label, png_uri, ocr_uri FROM automlapp_page WHERE file_id IN ({str(file_ids)[1:-1]});'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchall()
		for row in response:
			ids.append(row[0])
			png_uris.append(row[1])
			ocr_uris.append(row[2])
	except Exception as e:
		print("get_pages_of_files : ERROR : " + str(e))
	finally:
		db.close()
	return ids, png_uris, ocr_uris

def delete_file_from_rds(username, file_uri):

	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)

		query = f"DELETE FROM automlapp_file WHERE uri ='{file_uri}';"
		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
	except Exception as e:
		print("delete_file_from_rds : ERROR : " + str(e))
	finally:
		db.close()

def update_ocr_uri_by_page_id(page_id, ocr_uri):
	print(f"update_ocr_uri_by_page_id : INFO : page_id = {page_id}, ocr_uri = {ocr_uri}")
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)

		query = f'UPDATE automlapp_page SET ocr_uri = "{ocr_uri}" where id = {page_id};'
		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
	except Exception as e:
		print("update_ocr_uri_by_page_id : ERROR : " + str(e))
	finally:
		db.close()

def create_training_job(model_id: int, output_path: str) -> int:
	pk = -1
	try:
		project_id = get_project_id_by_model_id(model_id)
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)

		query = f'INSERT INTO automlapp_job(status, model_id, result, job_type, output_path, project_id) VALUES ("CREATED", {model_id}, 0, "TRAIN", "{output_path}", {project_id});'
		cursor = db.cursor()
		cursor.execute(query)
		pk = cursor.lastrowid
		db.commit()
	except mysql.IntegrityError:
		pass
	except Exception as e:
		print("create_training_job : ERROR : " + str(e))
	finally:
		db.close()
	return pk

def get_file_ids_preprocessed_untrained(project_id):
	ids = []
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT id FROM automlapp_file WHERE project_id = {project_id} AND trained = 0 AND preprocessed = 1;'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchall()
		for row in response:
			ids.append(int(row[0]))
	except Exception as e:
		print("get_file_ids_preprocessed_untrained : ERROR : " + str(e))
	finally:
		db.close()
	return ids

def get_model_hyperparams(model_id):
	hyperparams = {}
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT hyperparams FROM automlapp_modelversion WHERE id = {model_id};'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response[0] != None:
			hyperparams_json = json.loads(response[0])
			for key in hyperparams_json:
				hyperparams[key.upper()] = hyperparams_json[key]
	except Exception as e:
		print("get_model_hyperparams : ERROR : " + str(e))
	finally:
		db.close()
	return hyperparams

def get_trained_model_path(model_id):
	path = ''
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT trained_model_path FROM automlapp_modelversion WHERE id = {model_id};'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response[0] != None:
			path = response[0]
	except Exception as e:
		print("get_trained_model_path : ERROR : " + str(e))
	finally:
		db.close()
	return path

def get_trainings_for_project(project_id):
	trainings = 0
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT trainings FROM automlapp_project WHERE id = {project_id};'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response[0] != None:
			trainings = int(response[0])
	except Exception as e:
		print("get_trainings_for_project : ERROR : " + str(e))
	finally:
		db.close()
	return trainings

def get_raw_model_name_of_model_version(model_id):
	raw_model_name = ''
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query1 = f'SELECT raw_model_id FROM automlapp_modelversion WHERE id = {model_id};'
		cursor = db.cursor()
		cursor.execute(query1)
		response = cursor.fetchone()
		raw_model_id = int(response[0])
		query2 = f'SELECT name FROM automlapp_rawmodel WHERE id = {raw_model_id};'
		cursor.execute(query2)
		response = cursor.fetchone()
		raw_model_name = str(response[0])
	except Exception as e:
		print("get_raw_model_name_of_model_version : ERROR : " + str(e))
	finally:
		db.close()
	return raw_model_name

def get_model_ids_for_project(project_id):
	ids = []
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT id FROM automlapp_modelversion WHERE project_id = {project_id};'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchall()
		for row in response:
			ids.append(int(row[0]))
	except Exception as e:
		print("get_model_ids_for_project : ERROR : " + str(e))
	finally:
		db.close()
	return ids

def get_best_model_id_and_accuracy_for_project(project_id):
	id = -1
	ac = 0.0
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT id, accuracy FROM automlapp_modelversion WHERE project_id = {project_id};'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchall()
		for row in response:
			next_id = int(row[0])
			next_ac = float(row[1])
			if next_ac >= ac:
				id = next_id
				ac = next_ac
	except Exception as e:
		print("get_best_model_for_project : ERROR : " + str(e))
	finally:
		db.close()
	return id, ac

def get_training_image_tag_for_model_version(model_id):
	training_image = ''
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		cursor = db.cursor()
		query1 = f'select raw_model_id from automlapp_modelversion WHERE id = {model_id};'
		cursor.execute(query1)
		response = cursor.fetchone()
		raw_model_id = int(response[0])
		query2 = f'SELECT tag FROM automlapp_trainingimage WHERE id IN (SELECT training_image_id FROM automlapp_rawmodel WHERE id = {raw_model_id});'
		cursor.execute(query2)
		response = cursor.fetchone()
		training_image = str(response[0])
	except Exception as e:
		print("get_training_image_tag_for_model_version : ERROR : " + str(e))
	finally:
		db.close()
	return training_image

def update_trained_model_path(model_id, trained_model_path):
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)

		query = f'UPDATE automlapp_modelversion SET trained_model_path = "{trained_model_path}" where id = {model_id};'
		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
	except Exception as e:
		print("update_trained_model_path : ERROR : " + str(e))
	finally:
		db.close()

def tag_file(file_id, label):
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)

		query = f'UPDATE automlapp_file SET label = {label} where id = {file_id};'
		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
	except Exception as e:
		print("tag_file : ERROR : " + str(e))
	finally:
		db.close()

def get_last_used_port():
	last_used_port = 79
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT MAX(lb_port) FROM automlapp_project;"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response:
			last_used_port = int(response[0])
	except Exception as e:
		print("get_last_used_port : ERROR : " + str(e))
	finally:
		db.close()
	return last_used_port

def get_project_files(project_pk):
	uris = []
	labels = []
	npages = []
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f'SELECT uri, label, npages FROM automlapp_file WHERE project_id = {project_pk};'
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchall()
		for row in response:
			uris.append(row[0])
			labels.append(row[1])
			npages.append(int(row[2]))
	except Exception as e:
		print("get_project_files : ERROR : " + str(e))
	finally:
		db.close()
	return uris, labels, npages

def get_project_confianza(project_pk):
	confianza = 0
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT confianza FROM automlapp_project WHERE id = {project_pk};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response:
			confianza = int(response[0])
	except Exception as e:
		print("get_project_confianza : ERROR : " + str(e))
	finally:
		db.close()
	return confianza

def get_project_port(project_pk):
	port = 80
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT lb_port FROM automlapp_project WHERE id = {project_pk};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response:
			port = int(response[0])
	except Exception as e:
		print("get_project_port : ERROR : " + str(e))
	finally:
		db.close()
	return port

def get_cluster_name_of_project(project_pk):
	cluster_name = ""
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)
		query = f"SELECT cluster_name FROM automlapp_project WHERE id = {project_pk};"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response:
			cluster_name = str(response[0])
	except Exception as e:
		print("v : ERROR : " + str(e))
	finally:
		db.close()
	return cluster_name
