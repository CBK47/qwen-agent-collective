import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkfc.request.v20230228.CreateFunctionRequest import CreateFunctionRequest

def main():
    access_key = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    region = os.getenv('ALIBABA_CLOUD_REGION')
    service_name = os.getenv('FC_SERVICE_NAME')
    function_name = os.getenv('FC_FUNCTION_NAME')
    runtime = os.getenv('FC_RUNTIME', 'python3.9')
    handler = os.getenv('FC_HANDLER', 'main.handler')
    oss_bucket = os.getenv('OSS_BUCKET')
    oss_object = os.getenv('OSS_OBJECT')

    if not all([access_key, access_secret, region, service_name, function_name]):
        raise ValueError("Missing required environment variables for Alibaba Cloud deployment")

    client = AcsClient(access_key, access_secret, region)

    request = CreateFunctionRequest()
    request.set_ServiceName(service_name)
    request.set_FunctionName(function_name)
    request.set_Runtime(runtime)
    request.set_Handler(handler)

    if oss_bucket and oss_object:
        request.set_CodeOSSBucket(oss_bucket)
        request.set_CodeOSSObject(oss_object)

    response = client.do_action_with_exception(request)
    print(response)

if __name__ == '__main__':
    main()
