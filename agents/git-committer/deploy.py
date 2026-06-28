from shared import deploy_harness

def main():
    config = {
        'agent_name': 'git-committer',
        'image': 'registry.cn-hangzhou.aliyuncs.com/git-committer/webui:latest',
        'ports': [8080],
        'region': 'cn-hangzhou',
        'instance_type': 'ecs.g6.large',
        'vpc_id': 'vpc-12345678',
        'security_group_id': 'sg-12345678',
        'subnet_id': 'subnet-12345678',
        'env_vars': {
            'GITHUB_TOKEN': 'your_token_here',
            'OTHER_VAR': 'value'
        }
    }
    deploy_harness(config)

if __name__ == '__main__':
    main()
