import boto3
import base64
import hmac
import hashlib
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, USER_POOL_ID, CLIENT_ID, CLIENT_SECRET

client_cognito = boto3.client('cognito-idp',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name='us-west-2')


def get_secret_hash(username):
	msg = username + CLIENT_ID
	dig = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
		msg = str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
	d2 = base64.b64encode(dig).decode()
	return d2

def sign_up_user(username, password, email):
	try:
		resp = client_cognito.sign_up(
			ClientId=CLIENT_ID,
			SecretHash=get_secret_hash(username),
			Username=username,
			Password=password,
			UserAttributes=[
			{
				'Name': "email",
				'Value': email
			}
			],
			ValidationData=[
				{
				'Name': "email",
				'Value': email
			},
			{
				'Name': "custom:username",
				'Value': username
			}
	])


	except client_cognito.exceptions.UsernameExistsException as e:
		return {"error": False,
				"success": True,
				"message": "This username already exists",
				"data": None}
	except client_cognito.exceptions.InvalidPasswordException as e:

		return {"error": False,
				"success": True,
				"message": "Password should have Caps, Special chars, Numbers",
				"data": None}
	except client_cognito.exceptions.UserLambdaValidationException as e:
		return {"error": False,
				"success": True,
				"message": "Email already exists",
				"data": None}

	except Exception as e:
		return {"error": False,
				"success": True,
				"message": str(e),
				"data": None}

	return {"error": False,
			"success": True,
			"message": "Please confirm your signup, check Email for validation code",
			"data": None}

def confirm_sign_up(username, code):
	try:
		response = client_cognito.confirm_sign_up(
		ClientId=CLIENT_ID,
		SecretHash=get_secret_hash(username),
		Username=username,
		ConfirmationCode=code,
		ForceAliasCreation=False,
	   )
	except client_cognito.exceptions.UserNotFoundException:
		return {"error": True, "success": False, "message": "Username doesnt exists"}
		# return event
	except client_cognito.exceptions.CodeMismatchException:
		return {"error": True, "success": False, "message": "Invalid Verification code"}

	except client_cognito.exceptions.NotAuthorizedException:
		return {"error": True, "success": False, "message": "User is already confirmed"}

	except Exception as e:
		return {"error": True, "success": False, "message": f"Unknown error {e.__str__()} "}

	# return event
	return {"error": False, "success": True, "message": "Username confirmed"}

def initiate_auth(username, password):
	secret_hash = get_secret_hash(username)
	try:
		resp = client_cognito.initiate_auth(
			# AuthFlow='USER_SRP_AUTH'|'REFRESH_TOKEN_AUTH'|'REFRESH_TOKEN'|'CUSTOM_AUTH'|'ADMIN_NO_SRP_AUTH'|'USER_PASSWORD_AUTH'|'ADMIN_USER_PASSWORD_AUTH',
			AuthFlow='USER_PASSWORD_AUTH',
			AuthParameters={
					'USERNAME': username,
					'SECRET_HASH': secret_hash,
					'PASSWORD': password
			},
			ClientId=CLIENT_ID,
		)

	except client_cognito.exceptions.NotAuthorizedException:
		return None, "The username or password is incorrect"
	except client_cognito.exceptions.UserNotConfirmedException:
		return None, "User is not confirmed"
	except Exception as e:
		return None, e.__str__()
	return resp, None

def signin_user(username, password):
	resp, msg = initiate_auth(username, password)
	if msg != None:
		return {'message': msg,
			"error": True,
			"success": False,
			"data": None}

	if resp.get("AuthenticationResult"):
		return {'message': "success",
			"error": False,
			"success": True,
			"data": {
			"id_token": resp["AuthenticationResult"]["IdToken"],
			"refresh_token": resp["AuthenticationResult"]["RefreshToken"],
			"access_token": resp["AuthenticationResult"]["AccessToken"],
			"expires_in": resp["AuthenticationResult"]["ExpiresIn"],
			"token_type": resp["AuthenticationResult"]["TokenType"]
		  }}
	else: #this code block is relevant only when MFA is enabled
		return {"error": True,
			"success": False,
			"data": None, "message": None}
