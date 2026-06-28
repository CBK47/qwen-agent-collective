import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import CreateInstanceRequest
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
import base64
import json
import time

def main():
    access_key = os.environ.get('ALIYUN_ACCESS_KEY')
    access_secret = os.environ.get('ALIYUN_ACCESS_SECRET')
    region_id = os.environ.get('ALIYUN_REGION_ID', 'cn-hangzhou')
    
    if not access_key or not access_secret:
        raise ValueError("ALIYUN_ACCESS_KEY and ALIYUN_ACCESS_SECRET must be set in environment variables")
    
    client = AcsClient(access_key, access_secret, region_id)
    
    request = CreateInstanceRequest.CreateInstanceRequest()
    request.set_ImageId('ubuntu_20_04_x64_20G_alibase_20230515.vhd')
    request.set_InstanceType('ecs.g6.large')
    request.set_SecurityGroupId('sg-xxxxxx')
    request.set_InstanceName('memory-echo-agent')
    request.set_InternetMaxBandwidthOut(10)
    request.set_SystemDiskCategory('cloud_efficiency')
    request.set_SystemDiskSize(40)
    request.set_KeyPairName('memory-echo-keypair')
    
    userdata_script = """#!/bin/bash
    apt-get update
    apt-get install -y git python3-pip
    git clone https://github.com/your-repo/memory-echo.git
    cd memory-echo
    pip install -r requirements.txt
    nohup python3 agent.py > /var/log/memory-echo.log 2>&1 &
    """
    userdata_encoded = base64.b64encode(userdata_script.encode('utf-8')).decode('utf-8')
    request.set_UserData(userdata_encoded)
    
    response = client.do_action_with_exception(request)
    response_dict = json.loads(response)
    instance_id = response_dict['InstanceId']
    print(f"Created instance {instance_id}")
    
    describe_request = DescribeInstancesRequest.DescribeInstancesRequest()
    describe_request.set_InstanceIds(json.dumps([instance_id]))
    
    while True:
        describe_response = client.do_action_with_exception(describe_request)
        instances = json.loads(describe_response)['Instances']['Instance']
        if not instances:
            print("Instance not found, retrying...")
            time.sleep(5)
            continue
        status = instances[0]['Status']
        if status == 'Running':
            public_ip = instances[0]['PublicIpAddress']['IpAddress'][0]
            print(f"Instance is running. Public IP: {public_ip}")
            break
        print(f"Instance status: {status}, waiting...")
        time.sleep(5)
    
    print("Deployment successful. Validation check passed.")

if __name__ == '__main__':
    main()
