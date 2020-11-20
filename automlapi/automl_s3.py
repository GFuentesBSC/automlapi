import boto3
import zipfile
import os
from tqdm import tqdm
import copy
import json
import botocore.exceptions
import io
from botocore.exceptions import ClientError
from PyPDF2 import PdfFileReader
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY


client_s3 = boto3.client('s3',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')

resource_s3 = boto3.resource('s3',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')

def write_file(filepath, content):
	bucketName = "elasticbeanstalk-us-west-2-749868801319"
	bucket = resource_s3.Bucket(bucketName)
	try:
		object = bucket.Object(filepath)
		object.put(Body=content)
	except ClientError as e:
		print(str(e))

def delete_file_from_s3(username, file_uri):
	bname = get_bucketname_by_username(username)
	try:
		resource_s3.Object(bname, file_uri).delete()
	except Exception as e:
		print(f"delete_file_from_s3 : ERROR : {e}")

def upload_fileobj(file, bucket, key):
	client_s3.upload_fileobj(file, bucket, key)

def upload_document_to_s3(file, username, project_name):
	# TODO: Count npages of each document!!!
	s3_data_folder = f'user_data/{username}/{project_name}/data/raw_files/'
	filename, extension = os.path.splitext(file.name)

	new_pdfs = {}
	known_tags = {}
	extra_tags = {}

	if extension == '.pdf':
		s3_pdf_path = os.path.join(s3_data_folder, os.path.basename(file.name))
		content = file.read()
		file_copy = io.BytesIO(content)
		file_copy2 = io.BytesIO(content)
		npages = PdfFileReader(file_copy).getNumPages()
		print(f"upload_document_to_s3 : INFO : uploading {s3_pdf_path}...")
		private_upload_file(file_copy2, username, s3_pdf_path)
		new_pdfs[s3_pdf_path] = {}
		new_pdfs[s3_pdf_path]['label'] = -1
		new_pdfs[s3_pdf_path]['npages'] = npages
	else:
		classes = get_project_classes(username, project_name)
		if extension == '.tag':
			print(f"upload_document_to_s3 : INFO : a .tag file was uploaded!")
			content = file.read().decode('utf-8').lower()
			try:
				label = classes.index(content)
				print(f"upload_document_to_s3 : INFO : label = {label}")
				s3_pdf_path = os.path.join(s3_data_folder, os.path.basename(file.name))
				s3_pdf_path = s3_pdf_path.replace('.tag', '.pdf')
				extra_tags[s3_pdf_path] = label
			except ValueError:
				# si nos suben un unico fichero tag, con la clase mal puesta no hacemos nada...
				pass

		elif extension == '.zip':
			unzipped = zipfile.ZipFile(file)
			file_names = unzipped.namelist()
			for file_name in file_names:
				_, suf_file_ext = os.path.splitext(file_name)
				sub_file = unzipped.open(file_name)
				if suf_file_ext == '.pdf':
					s3_pdf_path = os.path.join(s3_data_folder, os.path.basename(file_name))
					content = sub_file.read()
					file_copy = io.BytesIO(content)
					file_copy2 = io.BytesIO(content)
					npages = PdfFileReader(file_copy).getNumPages()
					private_upload_file(file_copy2, username, s3_pdf_path)
					new_pdfs[s3_pdf_path] = {}
					new_pdfs[s3_pdf_path]['label'] = -1
					new_pdfs[s3_pdf_path]['npages'] = npages
				elif suf_file_ext == '.tag':
					s3_pdf_path = os.path.join(s3_data_folder, os.path.basename(file_name))
					s3_pdf_path= s3_pdf_path.replace('.tag', '.pdf')
					content = unzipped.read(file_name).decode('utf-8').lower()
					label = classes.index(content)
					known_tags[s3_pdf_path] = label

			# Check for matches between .pdf & .tag
			for entry in known_tags:
				if entry in new_pdfs:
					new_pdfs[entry]['label'] = known_tags[entry]
				else:
					extra_tags[entry] = known_tags[entry]

	return new_pdfs, extra_tags

def get_file(username: str,
             path: str) -> bytes:
    """
    """
    # TODO: use username's specific bucket
    bucketName = "elasticbeanstalk-us-west-2-749868801319"
    return client_s3.get_object(Bucket=bucketName, Key=path)

def download_file_from_s3(username, objectname, local_file):
	try:
		bucketName = get_bucketname_by_username(username)
		bucket = resource_s3.Bucket(bucketName)
		bucket.download_file(objectname, local_file)
		return True
	except Exception as e:
		print(f"download_file_from_s3 : ERROR : {e}")
		return False

def download_directory(bucketName, s3_dirname, local_dirname):
	if not os.path.exists(local_dirname):
		os.makedirs(local_dirname)
	bucket = resource_s3.Bucket(bucketName)
	for object in tqdm(bucket.objects.filter(Prefix = s3_dirname)):
		filename = os.path.basename(object.key)
		if filename != '':
			local_file = os.path.join(local_dirname, filename)
			bucket.download_file(object.key, local_file)

def get_bucketname_by_username(username):
	# TODO: Hacer una query a la tabla user para ver que bucket tiene asociado
	return 'elasticbeanstalk-us-west-2-749868801319'

def upload_file(file, username, objectname):
	# file must be opened in 'rb'
	try:
		bucketname = get_bucketname_by_username(username)
		print("Storing in " + bucketname + ": " + objectname)
		client_s3.upload_fileobj(file, bucketname, objectname)
		obj_summary = resource_s3.ObjectSummary(bucketname, objectname)
		print("File size: " + str(obj_summary.size) + " Bytes")
		return True
	except Exception as e:
		print("upload-upload_file : ERROR : " + str(e))
		return False

def private_upload_file(file, username, s3_path):
	try:
		bname = get_bucketname_by_username(username)
		client_s3.upload_fileobj(file, bname, s3_path)
		return True
	except Exception as e:
		print("private_upload_file : ERROR : " + str(e))
		return False

def get_folder_size(bucket, prefix):
	# RETURNS FOLDER SIZE IN MB
	# AWS CONSOLE RETURNS SIZE IN MiB
	# 1 MiB = 1,04858 MB
	total_size = 0
	for obj in resource_s3.Bucket(bucket).objects.filter(Prefix=prefix):
		total_size += obj.size
		return total_size

def upload_folder_as_zip(local_folder, s3_folder, username):

	def zipdir(path, ziph):
		for root, dirs, files in os.walk(path):
			for file in files:
				ziph.write(os.path.join(root, file))

	zip_name = f'{local_folder}.zip'
	with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
		zipdir(local_folder, zipf)
	zipf = open(zip_name, 'rb')
	objectname = s3_folder + '/' + zip_name
	upload_file(zipf, username, objectname)

def update_checkpoints(local_chkpts_dir, s3_chkpts_dir, username):
	for item in os.listdir(local_chkpts_dir):
		with open(os.path.join(local_chkpts_dir, item), 'rb') as f:
			objectname = s3_chkpts_dir + '/' + item
			upload_file(f, username, objectname)

def get_project_classes(username, project_name):
	objectname = f'user_data/{username}/{project_name}/data/index.txt'
	local_file = f'index.txt'
	download_file_from_s3(username, objectname, local_file)
	return [x.lower() for x in open(local_file, 'r').read().split(',')]
