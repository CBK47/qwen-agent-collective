import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkfc.request.v20160815 import CreateServiceRequest, CreateFunctionRequest

def get_client():
    access_key = os.getenv('ALIYUN_ACCESS_KEY_ID')
    secret_key = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
    region = os.getenv('ALIYUN_REGION', 'cn-hangzhou')
    return AcsClient(access_key, secret_key, region)

def deploy():
    client = get_client()
    
    service_name = 'skippy-concierge'
    create_service_req = CreateServiceRequest()
    create_service_req.set_ServiceName(service_name)
    create_service_req.set_Role('acs:ram::1234567890123456:role/aliyunfcdefaultrole')
    create_service_req.set_Description('Skippy Concierge Service for Alibaba Cloud')
    response = client.do_action_with_exception(create_service_req)
    print(f"Service created: {response}")
    
    function_name = 'concierge'
    create_function_req = CreateFunctionRequest()
    create_function_req.set_ServiceName(service_name)
    create_function_req.set_FunctionName(function_name)
    create_function_req.set_Handler('index.handler')
    create_function_req.set_Runtime('python3')
    create_function_req.set_CodeOSSBucket('skippy-concierge-code')
    create_function_req.set_CodeOSSKey('code.zip')
    response = client.do_action_with_exception(create_function_req)
    print(f"Function created: {response}")

if __name__ == '__main__':
    deploy()
