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
    rows_updated = 0
    try:
        db = mysql.connect(host=BD_HOST,
                database=BD_DATABASE,
                user=BD_USER,
                password=BD_PASS)

        cursor = db.cursor()
        if isinstance(query, list):
            for subquery in query:
                rows_updated += cursor.execute(subquery)
        else:
            rows_updated += cursor.execute(query)
        db.commit()
    except Exception as e:
        print("run_update - ERROR " + str(e))
    finally:
        db.close()
        return rows_updated

def run_delete(query):
	try:
		db = mysql.connect(host=BD_HOST,
							database=BD_DATABASE,
							user=BD_USER,
							password=BD_PASS)

		cursor = db.cursor()
		cursor.execute(query)
		db.commit()
	except Exception as e:
		print("run_delete - ERROR " + str(e))
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

def update_object_by_conditions(objectName, fields, conditions):

    parsed_fields = ""
    parsed_conditions = ""
    for key in fields:
        value = fields[key]
        if value is None:
            parsed_fields += f'{key} = NULL, '
        else:
            if isinstance(value, str):
                value = '"' + value + '"'
            parsed_fields += f'{key} = {value}, '
    else:
        parsed_fields = parsed_fields[:-2]

    for key in conditions:
        operator = '='
        value = conditions[key]
        if value is None:
            parsed_conditions += f'{key} is NULL AND '
        else:
            if isinstance(value, list):
                operator = 'IN'
                value = '(' + str(value)[1:-1] + ')'
            elif isinstance(value, str):
                value = '"' + value + '"'
            parsed_conditions += f'{key} {operator} {value} AND '
    else:
        parsed_conditions = parsed_conditions[:-4]
    query = f'UPDATE neuralplatform_{objectName.lower()} SET {parsed_fields} WHERE {parsed_conditions};'
    return run_update(query)

def get_pagesInfo_of_request(request_id):
    pagesInfo = {"pagesInfo": []}
    request   = get_n_objects_by_key('request', 1, 'id', request_id)[0]
    pages     = get_n_objects_by_key('productionPage', None, 'productionDocument_id', int(request['productionDocument_id'])) or []
    for page in pages:
        class_name = ""
        if page['tagged']:
            classification = get_n_objects_by_key('ProductionClassification', 1, 'productionPage_id', int(page['id']))[0]
            class_id = int(classification['classDefinition_id'])
            class_name = get_n_objects_by_key('classDefinition', 1, 'id', class_id)[0]['name']
        pagesInfo['pagesInfo'].append({"uri": page['imgUri'], "class": class_name})
    return pagesInfo

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
                value = "'" + value + "'"
            changes += field + ' = ' + str(value) + ', '
        else:
            changes = changes[:-2]
        query = f'UPDATE neuralplatform_{objectName.lower()} SET {changes} WHERE {key} {operator} {keyValue};'
        return run_update(query)
    else:
        return 0

def exists_object(objectName, conditions):
    parsed_conditions = ""
    for key in conditions:
        operator = '='
        value = conditions[key]
        if value is None:
            parsed_conditions += f'{key} is NULL AND '
        else:
            if isinstance(value, list):
                operator = 'IN'
                value = '(' + str(value)[1:-1] + ')'
            elif isinstance(value, str):
                value = '"' + value + '"'
            parsed_conditions += f'{key} {operator} {value} AND '
    else:
        parsed_conditions = parsed_conditions[:-4]
    query = f'SELECT * FROM neuralplatform_{objectName.lower()} WHERE {parsed_conditions};'
    return run_exists(query)

def get_objects_by_conditions(objectName, conditions):
    parsed_conditions = ""
    for key in conditions:
        operator = '='
        value = conditions[key]
        if value is None:
            parsed_conditions += f'{key} is NULL AND '
        else:
            if isinstance(value, list):
                operator = 'IN'
                value = '(' + str(value)[1:-1] + ')'
            elif isinstance(value, str):
                value = '"' + value + '"'
            parsed_conditions += f'{key} {operator} {value} AND '
    else:
        parsed_conditions = parsed_conditions[:-4]
    query = f'SELECT * FROM neuralplatform_{objectName.lower()} WHERE {parsed_conditions};'
    return run_select(query)

def get_object_count_by_conditions(objectName, conditions):
    parsed_conditions = ""
    for key in conditions:
        operator = '='
        value = conditions[key]
        if value is None:
            parsed_conditions += f'{key} is NULL AND '
        else:
            if isinstance(value, list):
                operator = 'IN'
                value = '(' + str(value)[1:-1] + ')'
            elif isinstance(value, str):
                value = '"' + value + '"'
            parsed_conditions += f'{key} {operator} {value} AND '
    else:
        parsed_conditions = parsed_conditions[:-4]
        query = f'SELECT COUNT(*) AS result FROM neuralplatform_{objectName.lower()} WHERE {parsed_conditions};'
    try:
        return int(run_select(query)[0]['result'])
    except Exception as e:
        print(f"get_object_count_by_conditions : ERROR : {e}")
        return 0

def get_projects_of_projectManager(projectManager_id):
	query = f"SELECT project_id FROM neuralplatform_projectmanagerassignedproject WHERE projectManager_id = {projectManager_id};"
	project_ids = run_select(query)
	return project_ids

def get_bucketName_by_page_id(page_id):
    try:
        query = "SELECT s3Bucket FROM neuralplatform_account WHERE id = " + \
            "(SELECT account_id FROM neuralplatform_project WHERE id = " + \
            "(SELECT project_id FROM neuralplatform_document WHERE id = " + \
            f"(SELECT document_id FROM neuralplatform_page WHERE id = {page_id})));"
        return run_select(query)[0]['s3Bucket']
    except Exception as e:
        print(f"get_bucketName_by_page_id : Error : {e}")
        return ""

def get_bucketName_by_productionPage_id(productionPage_id):
    try:
        query = "SELECT s3Bucket FROM neuralplatform_account WHERE id = " + \
            "(SELECT account_id FROM neuralplatform_project WHERE id = " + \
            "(SELECT project_id FROM neuralplatform_productiondocument WHERE id = " + \
            f"(SELECT productionDocument_id FROM neuralplatform_productionpage WHERE id = {productionPage_id})));"
        return run_select(query)[0]['s3Bucket']
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

def insert_document(uploadDate, filename, extension, uri, nPages, training, dataset_id, uploadMethod_id, project_id):
	query = f'INSERT INTO neuralplatform_document(uploadDate, name, extension, uri, nPages, training, dataset_id, uploadMethod_id, project_id) ' + \
			f'VALUES ("{uploadDate}", "{filename}", "{extension}", "{uri}", {nPages}, {training}, {dataset_id}, {uploadMethod_id}, {project_id});'
	return run_insert(query)

def insert_productionDocument(uploadDate, filename, extension, uri, nPages, training, uploadMethod_id, project_id):
	query = f'INSERT INTO neuralplatform_productiondocument(uploadDate, name, extension, uri, nPages, training, uploadMethod_id, project_id) ' + \
		f'VALUES ("{uploadDate}", "{filename}", "{extension}", "{uri}", {nPages}, {training}, {uploadMethod_id}, {project_id});'
	return run_insert(query)

def insert_request(phase, requestDate, productionDocument_id, project_id):
    emptyJson = '"{}"'
    query = f'INSERT INTO neuralplatform_request(phase, requestDate, productionDocument_id, project_id, response, status) ' + \
            f'VALUES ("{phase}", "{requestDate}", {productionDocument_id}, {project_id}, {emptyJson}, "pending");'
    return run_insert(query)

def insert_page(imgUri, ocrUri, document_id):
    query = f'INSERT INTO neuralplatform_page(imgUri, ocrUri, document_id) ' + \
            f'VALUES ("{imgUri}", "{ocrUri}", {document_id});'
    return run_insert(query)

def insert_productionPage(imgUri, ocrUri, productionDocument_id):
    query = f'INSERT INTO neuralplatform_productionpage(imgUri, ocrUri, productionDocument_id) ' + \
            f'VALUES ("{imgUri}", "{ocrUri}", {productionDocument_id});'
    return run_insert(query)

def insert_productionLog(eventTime, event, account_id, project_id, request_id, eventData={}):
    query = f'INSERT INTO neuralplatform_productionlog(eventTime, event, account_id, project_id, request_id, eventData) ' + \
            f"VALUES ({eventTime}, '{event}', {account_id}, {project_id}, {request_id}, '{json.dumps(eventData)}');"
    return run_insert(query)

def get_pending_and_unblocked_steps():
    # TODO: # OPTIMIZE:  this
    # query1 = 'SELECT neuralplatform_step.id, neuralplatform_request.requestDate FROM neuralplatform_step INNER JOIN ' + \
    #          'neuralplatform_request ON neuralplatform_step.request_id=neuralplatform_request.id WHERE neuralplatform_step.status = "pending" ORDER BY neuralplatform_request.requestDate ASC;'
    unblocked_steps = []
    querySD = 'SELECT id, blockingStep_id FROM neuralplatform_stepdefinition;'
    stepDefinitions = run_select(querySD)
    dependencies = {s['id']: s['blockingStep_id'] for s in stepDefinitions}
    for request in run_select('SELECT * FROM neuralplatform_request WHERE status = "running" ORDER BY id ASC;'):
        query1 = f'SELECT * FROM neuralplatform_step WHERE status = "pending" AND request_id = {int(request["id"])};'
        pending_steps = run_select(query1)
        if len(pending_steps) > 0:
            pending_stepDefinitions = list(set([x['stepDefinition_id'] for x in pending_steps]))
            unblocked_stepDefinitions = []
            for pending_stepDefinition in pending_stepDefinitions:
                sd_dependency = dependencies[pending_stepDefinition] or -1
                if not run_exists(f'SELECT id FROM neuralplatform_step WHERE status NOT IN ("succeeded") AND stepDefinition_id = {sd_dependency} AND request_id = {int(request["id"])};'):
                    unblocked_stepDefinitions.append(pending_stepDefinition)
            unblocked_steps += list(filter(lambda x: x['stepDefinition_id'] in unblocked_stepDefinitions, pending_steps))
    return unblocked_steps

def classify_page(page_id, class_id, manual=False):
    if run_exists(f"SELECT DISTINCT 1 FROM neuralplatform_classification WHERE page_id = {page_id};"):
        run_delete(f"DELETE FROM neuralplatform_classification WHERE page_id = {page_id};")
    run_insert(f"INSERT INTO neuralplatform_classification(classDefinition_id, page_id, manual) VALUES ({class_id}, {page_id}, {manual});")
    update_object_by_key('page', 'id', page_id, {'tagged': True})

def classify_productionPage(productionPage_id, class_id, manual=False):
    if run_exists(f"SELECT DISTINCT 1 FROM neuralplatform_productionclassification WHERE productionPage_id = {productionPage_id};"):
        run_delete(f"DELETE FROM neuralplatform_productionclassification WHERE productionPage_id = {productionPage_id};")
    run_insert(f"INSERT INTO neuralplatform_productionclassification(classDefinition_id, productionPage_id, manual) VALUES ({class_id}, {productionPage_id}, {manual});")
    update_object_by_key('productionPage', 'id', productionPage_id, {'tagged': True})

def get_train_untagged_documents_by_project(project_id, limit=None):
	query = f"SELECT * FROM neuralplatform_document WHERE project_id = {project_id} AND EXISTS " + \
            f"(SELECT id FROM neuralplatform_page WHERE neuralplatform_page.document_id = neuralplatform_document.id AND neuralplatform_page.tagged = 0)" + \
            (f" LIMIT {limit};" if limit else ";")
	return run_select(query)

def insert_manualStep(result, request_id):
    query = f"INSERT INTO neuralplatform_manualstep(status, result, request_id) " + \
            f"VALUES ('pending', '{json.dumps(result)}', {request_id});"
    return run_insert(query)

def get_requests_status_count_by_project_ids(project_ids, status):
    projects = '(' + str(project_ids)[1:-1] + ')'
    query = f'SELECT neuralplatform_project.id AS project, COUNT(neuralplatform_request.id) AS counter ' + \
            f'FROM neuralplatform_project LEFT JOIN neuralplatform_request ON neuralplatform_project.id = neuralplatform_request.project_id ' + \
            f'AND neuralplatform_request.status = "{status}" WHERE neuralplatform_project.id IN {projects} ' + \
            f'GROUP BY neuralplatform_project.id;'
    try:
        retval = run_select(query)
        result = {}
        for row in retval:
            result[row['project']] = row['counter']
        return result
    except Exception as e:
        print(f'get_requests_status_count_by_project_ids : ERROR : {e}')
        return []
