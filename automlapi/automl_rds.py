import MySQLdb as mysql
import os
import json
from .automl import BD_HOST, BD_PASS

##################### RDS #############################
def get_projects_of_user(user_pk):

	project_names = []

	try:
		db = mysql.connect(host=BD_HOST,
							 database='ebdb',
							 user='admin',
							 password=BD_PASS)
		query = "SELECT proj_name FROM automlapp_project WHERE user_id = " + str(user_pk) + ";"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchall()
		for elem in response:
			project_names.append(elem[0])
	except:
		print("get_projects_of_user - ERROR")
	finally:
		cursor.close()
		db.close()
	return project_names

def get_user_pk_by_username(username):
	pk = -1
	try:
		db = mysql.connect(host=BD_HOST,
							database='ebdb',
							user='admin',
							password=BD_PASS)
		query = f"SELECT id FROM automlapp_user WHERE username = '{username}';"
		cursor = db.cursor()
		cursor.execute(query)
		response = cursor.fetchone()
		if response:
			pk = int(response[0])
	except:
		print("get_user_pk_by_username - ERROR")
	finally:
		db.close()
	return pk

def get_user_pk_by_username_password(username, password):
	pk = -1
	try:
		db = mysql.connect(host=BD_HOST,
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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

def insert_file(file_path, project_name, user_pk, npages=1):
	pk = -1
	try:
		db = mysql.connect(host=BD_HOST,
							database='ebdb',
							user='admin',
							password=BD_PASS)

		file_name, file_ext = os.path.splitext(os.path.basename(file_path))
		file_ext = file_ext.replace('.','')
		project_pk = get_project_pk_by_user_pk_project_name(user_pk, project_name)
		query = '''INSERT INTO automlapp_file(file_type, file_name, uri, project_id, trained, npages)
							VALUES("{}","{}","{}",{},{},{})'''.format(file_ext, file_name, file_path, project_pk, 0, npages)
		cursor = db.cursor()
		cursor.execute(query)
		pk = cursor.lastrowid
		db.commit()
	except mysql.IntegrityError:
		pass
	except Exception as e:
		print("insert_file : ERROR :  " + str(e))
	finally:
		db.close()
	return pk

def insert_files_to_rds(paths, project_name, user_pk):
	inserted = False
	try:
		db = mysql.connect(host=BD_HOST,
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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

def insert_page(image_path_s3, file_id, label):
	pk = -1
	try:
		db = mysql.connect(host=BD_HOST,
							database='ebdb',
							user='admin',
							password=BD_PASS)

		query = f'INSERT INTO automlapp_page(png_uri, file_id, label) VALUES ("{image_path_s3}", {file_id}, {label})'
		cursor = db.cursor()
		cursor.execute(query)
		pk = cursor.lastrowid
		db.commit()
	except mysql.IntegrityError:
		pass
	except Exception as e:
		print("insert_page : ERROR : " + str(e))
	finally:
		db.close()
	return pk

def get_trained_model_path(project_id):
	path = None
	try:
		db = mysql.connect(host=BD_HOST,
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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

def get_project_port(project_pk):
	port = 80
	try:
		db = mysql.connect(host=BD_HOST,
							database='ebdb',
							user='admin',
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
							database='ebdb',
							user='admin',
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
