import os
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkecs.request.v20140526 import (
    CreateSecurityGroupRequest,
    CreateSecurityGroupRuleRequest,
    CreateInstanceRequest,
    DescribeInstancesRequest
)
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
import subprocess

# Get Alibaba Cloud credentials from environment variables
access_key_id = os.getenv('ALIBABA_ACCESS_KEY_ID')
access_key_secret = os.getenv('ALIBABA_ACCESS_KEY_SECRET')
region_id = 'cn-hangzhou'

if not access_key_id or not access_key_secret:
    raise ValueError("ALIBABA_ACCESS_KEY_ID and ALIBABA_ACCESS_KEY_SECRET must be set in environment variables")

client = AcsClient(access_key_id, access_key_secret, region_id)

# Build Docker image for open-translate agent
print("Building Docker image...")
subprocess.run(['docker', 'build', '-t', 'open-translate-agent', '.'], check=True)

# Push to Alibaba Cloud Container Registry (ACR)
acr_registry = 'registry.cn-hangzhou.aliyuncs.com/open-translate/open-translate-agent'
print(f"Pushing image to ACR: {acr_registry}")

# Login to ACR using AccessKey
subprocess.run(['docker', 'login', '-u', access_key_id, '-p', access_key_secret, 'registry.cn-hangzhou.aliyuncs.com'], check=True)
subprocess.run(['docker', 'tag', 'open-translate-agent', acr_registry], check=True)
subprocess.run(['docker', 'push', acr_registry], check=True)

# Create security group
print("Creating security group...")
security_group_request = CreateSecurityGroupRequest.CreateSecurityGroupRequest()
security_group_request.set_GroupName('open-translate-security-group')
security_group_response = client.do_action_with_exception(security_group_request)
security_group_id = security_group_response['SecurityGroupId']

# Add security group rules for HTTP (port 80) and HTTPS (port 443)
print("Adding security group rules...")
http_rule_request = CreateSecurityGroupRuleRequest.CreateSecurityGroupRuleRequest()
http_rule_request.set_SecurityGroupId(security_group_id)
http_rule_request.set_IpProtocol('tcp')
http_rule_request.set_PortRange('80/80')
http_rule_request.set_SourceCidrIp('0.0.0.0/0')
http_rule_request.set_Priority(1)
client.do_action_with_exception(http_rule_request)

https_rule_request = CreateSecurityGroupRuleRequest.CreateSecurityGroupRuleRequest()
https_rule_request.set_SecurityGroupId(security_group_id)
https_rule_request.set_IpProtocol('tcp')
https_rule_request.set_PortRange('443/443')
https_rule_request.set_SourceCidrIp('0.0.0.0/0')
https_rule_request.set_Priority(2)
client.do_action_with_exception(https_rule_request)

# Create ECS instance with startup script
print("Creating ECS instance...")
startup_script = f"""#!/bin/bash
apt-get update
apt-get install -y docker.io
docker login -u {access_key_id} -p {access_key_secret} registry.cn-hangzhou.aliyuncs.com
docker pull {acr_registry}
docker run -d -p 80:80 -p 443:443 {acr_registry}
"""

instance_request = CreateInstanceRequest.CreateInstanceRequest()
instance_request.set_ImageId('ubuntu_20_04_x64_20G_alibase_20230515.vhd')
instance_request.set_InstanceType('ecs.g6.large')
instance_request.set_SecurityGroupId(security_group_id)
instance_request.set_SystemDiskCategory('cloud_efficiency')
instance_request.set_SystemDiskSize(40)
instance_request.set_InternetMaxBandwidthOut(5)
instance_request.set_InstanceName('open-translate-agent')
instance_request.set_UserData(startup_script)

instance_response = client.do_action_with_exception(instance_request)
instance_id = instance_response['InstanceId']

# Wait for instance to be running
print("Waiting for instance to start...")
while True:
    describe_request = DescribeInstancesRequest.DescribeInstancesRequest()
    describe_request.set_InstanceIds([instance_id])
    describe_response = client.do_action_with_exception(describe_request)
    instances = describe_response['Instances']['Instance']
    if instances and instances[0]['Status'] == 'Running':
        break
    time.sleep(5)

public_ip = instances[0]['PublicIpAddress']
print(f"Deployment successful! Instance ID: {instance_id}")
print(f"Open-translate agent is now accessible at http://{public_ip}")
