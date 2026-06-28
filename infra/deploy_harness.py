import base64
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

    def deploy_memory_echo(self, zone_id, instance_type, security_group_id, vswitch_id, image_id=None):
        if image_id is None:
            image_id = "m-xxxxxxxx"
        request = CreateInstanceRequest()
        request.set_ZoneId(zone_id)
        request.set_InstanceType(instance_type)
        request.set_ImageId(image_id)
        request.set_SecurityGroupId(security_group_id)
        request.set_VSwitchId(vswitch_id)
        request.set_InstanceName("MemoryEchoInstance")
        user_data_script = """#!/bin/bash
# Install memory-echo agent
curl -o /tmp/agent.sh https://example.com/memory-echo-agent.sh
chmod +x /tmp/agent.sh
/tmp/agent.sh
"""
        request.set_UserData(base64.b64encode(user_data_script.encode()).decode())
        response = self.client.do_action_with_exception(request)
        return response
