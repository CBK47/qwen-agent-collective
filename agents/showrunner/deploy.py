import os
import oss2
from aliyunsdkcore.client import AcsClient
from aliyunsdkfc.request.v20230228.CreateFunctionRequest import CreateFunctionRequest
from aliyunsdkfc.request.v20230228.GetServiceRequest import GetServiceRequest
from aliyunsdkfc.request.v20230228.CreateServiceRequest import CreateServiceRequest
from aliyunsdkfc.request.v20230228.GetFunctionRequest import GetFunctionRequest
from aliyunsdkfc.request.v20230228.UpdateFunctionRequest import UpdateFunctionRequest

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
    role_arn = os.getenv('FC_ROLE_ARN')

    if not all([access_key, access_secret, region, service_name, function_name, role_arn]):
        raise ValueError("Missing required environment variables for Alibaba Cloud deployment")

    client = AcsClient(access_key, access_secret, region)

    try:
        get_service_request = GetServiceRequest()
        get_service_request.set_ServiceName(service_name)
        client.do_action_with_exception(get_service_request)
    except Exception as e:
        if 'Service not found' in str(e) or '404' in str(e):
            create_service_request = CreateServiceRequest()
            create_service_request.set_ServiceName(service_name)
            create_service_request.set_Description('Showrunner service')
            create_service_request.set_Role(role_arn)
            client.do_action_with_exception(create_service_request)
        else:
            raise

    try:
        get_function_request = GetFunctionRequest()
        get_function_request.set_ServiceName(service_name)
        get_function_request.set_FunctionName(function_name)
        client.do_action_with_exception(get_function_request)
        
        update_request = UpdateFunctionRequest()
        update_request.set_ServiceName(service_name)
        update_request.set_FunctionName(function_name)
        update_request.set_Runtime(runtime)
        update_request.set_Handler(handler)
        if oss_bucket and oss_object:
            update_request.set_CodeOSSBucket(oss_bucket)
            update_request.set_CodeOSSObject(oss_object)
        response = client.do_action_with_exception(update_request)
    except Exception as e:
        if 'Function not found' in str(e) or '404' in str(e):
            create_request = CreateFunctionRequest()
            create_request.set_ServiceName(service_name)
            create_request.set_FunctionName(function_name)
            create_request.set_Runtime(runtime)
            create_request.set_Handler(handler)
            if oss_bucket and oss_object:
                create_request.set_CodeOSSBucket(oss_bucket)
                create_request.set_CodeOSSObject(oss_object)
            response = client.do_action_with_exception(create_request)
        else:
            raise

    video_file = os.getenv('VIDEO_FILE')
    video_object = os.getenv('VIDEO_OBJECT', 'video.mp4')
    if video_file:
        try:
            auth = oss2.Auth(access_key, access_secret)
            endpoint = f'oss-{region}.aliyuncs.com'
            bucket = oss2.Bucket(auth, endpoint, oss_bucket)
            with open(video_file, 'rb') as f:
                bucket.put_object(video_object, f)
            print(f"Video uploaded successfully to {oss_bucket}/{video_object}")
        except Exception as e:
            print(f"Error uploading video: {str(e)}")
            raise

    print(response)

if __name__ == '__main__':
    main()
