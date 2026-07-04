"""Deploy the Track 3 git-committer WebUI to Alibaba Cloud ECS.

This script is intentionally narrow for the Qwen Cloud hackathon submission: it
creates an ECS instance with user-data that checks out this repository, installs
the Python dependencies, and starts ``webui/server.mjs`` as a systemd service.

Required environment variables:
    ALIBABA_CLOUD_ACCESS_KEY_ID
    ALIBABA_CLOUD_ACCESS_KEY_SECRET
    ALIBABA_CLOUD_REGION
    ALIYUN_ZONE_ID
    ALIYUN_SECURITY_GROUP_ID
    ALIYUN_VSWITCH_ID
    ALIYUN_IMAGE_ID

The DashScope key is deliberately not embedded in ECS user-data. Put
``DASHSCOPE_API_KEY=...`` in ``/etc/qwen-agent-collective.env`` on the instance
through your normal secret-management path before running the public demo.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from textwrap import dedent

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkecs.request.v20140526.CreateInstanceRequest import CreateInstanceRequest
    from aliyunsdkecs.request.v20140526.StartInstanceRequest import StartInstanceRequest
except ImportError as exc:  # pragma: no cover - exercised only by deploy operators
    raise SystemExit(
        "Alibaba Cloud SDKs are required for deployment. Install with: "
        "python3 -m pip install aliyun-python-sdk-core aliyun-python-sdk-ecs"
    ) from exc


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def deployment_value(name: str, dry_run: bool) -> str:
    if dry_run:
        return os.getenv(name, f"dry-run-{name.lower().replace('_', '-')}")
    return required_env(name)


def build_user_data(repo_url: str, branch: str, port: int) -> str:
    script = f"""#!/usr/bin/env bash
set -euo pipefail

apt-get update
apt-get install -y git python3 python3-venv python3-pip nodejs npm

install -d -m 0755 /opt/qwen-agent-collective
if [ ! -d /opt/qwen-agent-collective/.git ]; then
  git clone --branch {branch} --depth 1 {repo_url} /opt/qwen-agent-collective
else
  git -C /opt/qwen-agent-collective fetch origin {branch}
  git -C /opt/qwen-agent-collective checkout {branch}
  git -C /opt/qwen-agent-collective pull --ff-only origin {branch}
fi

cd /opt/qwen-agent-collective
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

cat >/etc/systemd/system/qwen-git-committer.service <<'UNIT'
[Unit]
Description=Qwen Agent Collective Track 3 git-committer WebUI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/qwen-agent-collective
Environment=PORT={port}
EnvironmentFile=-/etc/qwen-agent-collective.env
ExecStart=/usr/bin/node webui/server.mjs
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now qwen-git-committer.service
"""
    return base64.b64encode(dedent(script).encode("utf-8")).decode("ascii")


def create_instance(args: argparse.Namespace) -> str:
    client = None
    if not args.dry_run:
        client = AcsClient(
            required_env("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            required_env("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
            args.region,
        )

    request = CreateInstanceRequest()
    request.set_accept_format("json")
    request.set_ZoneId(deployment_value("ALIYUN_ZONE_ID", args.dry_run))
    request.set_ImageId(deployment_value("ALIYUN_IMAGE_ID", args.dry_run))
    request.set_InstanceType(args.instance_type)
    request.set_SecurityGroupId(deployment_value("ALIYUN_SECURITY_GROUP_ID", args.dry_run))
    request.set_VSwitchId(deployment_value("ALIYUN_VSWITCH_ID", args.dry_run))
    request.set_InstanceName(args.instance_name)
    request.set_HostName(args.instance_name)
    request.set_InternetMaxBandwidthOut(args.internet_bandwidth_out)
    request.set_UserData(build_user_data(args.repo_url, args.branch, args.port))

    if args.dry_run:
        print("Dry run: ECS CreateInstanceRequest prepared for git-committer.")
        print(f"region={args.region} instance_type={args.instance_type} port={args.port}")
        return "dry-run"

    assert client is not None
    response = client.do_action_with_exception(request)
    payload = json.loads(response.decode("utf-8") if isinstance(response, bytes) else str(response))
    instance_id = payload["InstanceId"]

    start = StartInstanceRequest()
    start.set_accept_format("json")
    start.set_InstanceId(instance_id)
    client.do_action_with_exception(start)
    return instance_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Track 3 git-committer to Alibaba Cloud ECS.")
    parser.add_argument("--region", default=os.getenv("ALIBABA_CLOUD_REGION", "cn-hangzhou"))
    parser.add_argument("--instance-type", default=os.getenv("ALIYUN_INSTANCE_TYPE", "ecs.g7.large"))
    parser.add_argument("--instance-name", default="qwen-git-committer")
    parser.add_argument("--repo-url", default="https://github.com/CBK47/qwen-agent-collective.git")
    parser.add_argument("--branch", default="master")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--internet-bandwidth-out", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    instance_id = create_instance(args)
    print(f"git-committer deployment started: {instance_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
