from .automl_batch import *
from .automl_cloudwatch import *
from .automl_cognito import *
from .automl_rds import *
from .automl_s3 import *
import getpass
from django.shortcuts import get_object_or_404
import os
from tqdm import tqdm


class APIUser():

    def __init__(self):
        self.authenticated = False
        self.project_name = None
        self.login()

    def login(self):
        username = input("Username: ")
        password = getpass.getpass(prompt="Password: ")
        response = signin_user(username, password)
        if response['message'] == 'success':
            self.username = username
            self.password = password
            self.authenticated = True
            self.pk = get_user_pk_by_username_password(username, password)
            print("User and password correct")
        else:
            print("Wrong username or password")

    def upload_file(self, file_path):
        if self.authenticated:
            if None != self.project_name:
                file = open(file_path, "rb")
                response = upload_file_to_s3(file, self.username, self.project_name)
                paths = [ind_response[1] for ind_response in response if ind_response[0]]
                insert_files_to_rds(paths, self.project_name, self.pk)
                # for file_path in response:
                #     if ind_response[0]:
                #         if insert_file(str(ind_response[1]), self.project_name, self.pk):
                #             print("File uploaded: " + str(ind_response[1]))
                #         else:
                #             print("Database not updated for file: " + str(ind_response[1]))
                #     else:
                #         print("File could not be uploaded")
            else:
                # SELECT PROJECT first
                self.select_project()
        else:
            print("You are not logged-in, please log-in first")
            self.login()

    def select_project(self):
        if self.authenticated:
            project_names = get_projects_of_user(self.pk)
            if project_names == []:
                print("YOU DON'T HAVE PROJECTS!")
                return
            proj_name = ""
            while proj_name not in project_names:
                proj_name = input("Select one of your projects " + str(project_names) + ": ")
            self.project_name = proj_name
        else:
            print("You are not logged-in, please log-in first")
            self.login()



## PRIVATE FUNCTION TO UPLOAD DATASETS TO S3
def private_upload_dataset(folder, s3_folder):
    # s3_folder = 'data/CIFAR/train/'
    # s3_folder = 'data/CIFAR/validation/'
    os.chdir(folder)
    files = os.listdir()
    input("Gonna upload " + str(len(files)) + " files. Is that ok? ")
    for filename in tqdm(files):
        s3_path = os.path.join(s3_folder, filename)
        file = open(filename, "rb")
        if private_upload_file(file, s3_path) == False:
            print("path: " + s3_path)
            print("ERROR")
            break

## PRIVATE FUNCTION TO GENERATE 2 .LST FILES FROM A DIRECTORY (TRAIN AND TEST)
def make_lst(folder, ratio, extension):

    def find_label_in_name(filename, label_dict):
        for label in label_dict:
            if label in filename:
                return label_dict[label]
        return -1

    label_list = open(os.path.join(folder,'index.txt'), 'r').read().split(',')
    index = 0
    label_dict = dict()
    for l in label_list:
        label_dict[l] = index
        index += 1
    print("labels: " + str(label_dict))
    # filtrar los archivos de la carpeta por su extension (ex: si extension=='png' solo nos interesan los pngs)
    files = [x for x in os.listdir(folder) if x.endswith(extension.lower())]
    split_point = int(len(files)*ratio)
    train_files = files[:split_point]
    test_files = files[split_point:]

    train_lst_name = os.path.join(folder,'train.lst')
    test_lst_name = os.path.join(folder,'test.lst')
    errors_lst_name = os.path.join(folder,'errors.lst')
    f_train = open(train_lst_name, 'w')
    f_test = open(test_lst_name, 'w')
    f_errors = open(errors_lst_name, 'w')
    index = 0
    for filename in tqdm(train_files):
        label = find_label_in_name(filename, label_dict)
        row = str(index) + '\t' + str(label) + '\t' + filename
        if index < len(train_files) - 1:
            row += '\n'
        if label >= 0:
            f_train.write(row)
            index += 1
        else:
            f_errors.write(row)
    index = 0
    for filename in tqdm(test_files):
        label = find_label_in_name(filename, label_dict)
        row = str(index) + '\t' + str(label) + '\t' + filename
        if index < len(test_files) - 1:
            row += '\n'
        if label >= 0:
            f_test.write(row)
            index += 1
        else:
            f_errors.write(row)

    f_train.close()
    f_test.close()
    f_errors.close()
