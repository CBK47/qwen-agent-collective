from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.CreateInstanceRequest import CreateInstanceRequest

class AlibabaDeployHarness:
    def __init__(self, access_key_id, access_key_secret, region_id):
        self.client = AcsClient(access_key_id, access_key_secret, region_id)
    
    def deploy_ecs_instance(self, zone_id, instance_type, image_id, security_group_id, vswitch_id):
        request = CreateInstanceRequest()
        request.set_ZoneId(zone_id)
        request.set_InstanceType(instance_type)
        request.set_ImageId(image_id)
        request.set_SecurityGroupId(security_group_id)
        request.set_VSwitchId(vswitch_id)
        request.set_InstanceName("DeployedInstance")
        response = self.client.do_action_with_exception(request)
        return response
