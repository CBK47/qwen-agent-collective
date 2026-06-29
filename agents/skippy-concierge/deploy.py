import os
import zipfile
from aliyunsdkcore.client import AcsClient
from aliyunsdkfc.request.v20160815 import CreateServiceRequest, CreateFunctionRequest
import oss2

def get_client():
    access_key = os.getenv('ALIYUN_ACCESS_KEY_ID')
    secret_key = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
    region = os.getenv('ALIYUN_REGION', 'cn-hangzhou')
    return AcsClient(access_key, secret_key, region)

def deploy():
    client = get_client()
    access_key = os.getenv('ALIYUN_ACCESS_KEY_ID')
    secret_key = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
    region = os.getenv('ALIYUN_REGION', 'cn-hangzhou')
    endpoint = f'oss-{region}.aliyuncs.com'
    bucket_name = 'skippy-concierge-code'
    
    # Initialize OSS client and ensure bucket exists
    auth = oss2.Auth(access_key, secret_key)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    try:
        bucket.get_bucket_info()
    except oss2.exceptions.NoSuchBucket:
        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ)
    
    # Package and upload code to OSS
    with zipfile.ZipFile('code.zip', 'w') as zipf:
        for root, _, files in os.walk('.'):
            for file in files:
                if file != 'deploy.py':
                    zipf.write(os.path.join(root, file))
    bucket.put_object_from_file('code.zip', 'code.zip')
    
    # Deploy FC service and function
    service_name = 'skippy-concierge'
    create_service_req = CreateServiceRequest()
    create_service_req.set_ServiceName(service_name)
    create_service_req.set_Role(os.getenv('ALIYUN_ROLE_ARN'))
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
