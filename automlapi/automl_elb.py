import boto3
from .automl import AWS_ACC_KEY_ID, AWS_SEC_ACC_KEY, AWS_REGION_NAME

client_elb = boto3.client('elbv2',
						aws_access_key_id=AWS_ACC_KEY_ID,
						aws_secret_access_key=AWS_SEC_ACC_KEY,
						region_name=AWS_REGION_NAME)

def create_flask_target_group(name):
	response = client_elb.create_target_group(
	    Name=name,
	    Protocol='HTTP',
	    Port=5000,
	    VpcId='vpc-9c6422fa',
	    HealthCheckProtocol='HTTP',
	    HealthCheckPort='traffic-port',
	    HealthCheckEnabled=True,
	    HealthCheckPath='/healthcheck',
	    HealthCheckIntervalSeconds=30,
	    HealthCheckTimeoutSeconds=5,
	    HealthyThresholdCount=3,
	    UnhealthyThresholdCount=3,
	    Matcher={
	        'HttpCode': '200'
	    },
	    TargetType='instance',

	)
	if int(response['ResponseMetadata']['HTTPStatusCode']) == 200:
		print(f'create_flask_target_group : INFO : Created TargetGroup {name}!')
		return str(response['TargetGroups'][0]['TargetGroupArn'])
	else:
		print(f'create_flask_target_group : ERROR : Could not create TargetGroup {name}!')
		return False

def add_listener_to_load_balancer(port, mappings):
	response = client_elb.create_listener(
	    LoadBalancerArn='arn:aws:elasticloadbalancing:us-west-2:749868801319:loadbalancer/app/Flask-Services-LB/fc15f78a9d19b599',
	    Protocol='HTTP',
	    Port=port,
	    DefaultActions=[
	        {
	            'Type': 'fixed-response',
	            'FixedResponseConfig': {
	                'MessageBody': f'Usage: invoke a service from {list(mappings.keys())}',
	                'StatusCode': '503',
	                'ContentType': 'text/plain'
	            }
	        }
	    ]
	)

	if int(response['ResponseMetadata']['HTTPStatusCode']) == 200:
		print(f'add_listener_to_load_balancer : INFO : Added listener on port {port}!')
		listener_arn = response['Listeners'][0]['ListenerArn']
		print(f'add_listener_to_load_balancer : INFO : Adding traffic redirection rules...')
		return add_rules(listener_arn, mappings)
	return False

def add_rules(listener_arn, mappings):
	p = 0
	for path in mappings:
		p = p + 1
		response = client_elb.create_rule(
		    ListenerArn=listener_arn,
		    Conditions=[
		        {
		            'Field': 'path-pattern',
		            'PathPatternConfig': {
		                'Values': [f'/{path}']
		            }
		        }
		    ],
			Priority=p,
		    Actions=[
		        {
		            'Type': 'forward',
		            'ForwardConfig': {
		                'TargetGroups': [
		                    {
		                        'TargetGroupArn': mappings[path],
		                        'Weight': 1
		                    }
		                ]
		            }
		        }
		    ]
		)
		if response['ResponseMetadata']['HTTPStatusCode'] != 200:
			print(f'add_rules : ERROR : Oops! Could not add redirection rule for {path} -> {mappings[path]}')
			return False
		else:
			print(f'add_rules : INFO : Added rule for {path} -> {mappings[path]}')
	return True

def get_targets_health(target_group_arn):
	targets_health = client.describe_target_health(TargetGroupArn=target_group_arn)['TargetHealthDescriptions']
	return [x['TargetHealth']['State'] for x in targets_health]

def get_num_unhealthy_targets(target_group_arn):
	targets_health = get_targets_health(target_group_arn)
	return len(list(filter(lambda x: x.lower() == 'unhealthy', targets_health)))
