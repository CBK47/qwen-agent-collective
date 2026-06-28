# infra

Reusable Alibaba Cloud deployment harness for all agent tracks.

## Prerequisites

- Alibaba Cloud account with Access Key and Secret
- Terraform installed (version >= 1.0)
- [alicloud provider](https://www.terraform.io/docs/providers/alicloud/index.html) configured

## Setup Steps

1. **Configure Credentials**

   Copy the environment variables template and fill in your Alibaba Cloud credentials:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your Access Key ID, Secret Key, and region:

   ```env
   ALICLOUD_ACCESS_KEY="your_access_key"
   ALICLOUD_SECRET_KEY="your_secret_key"
   ALICLOUD_REGION="cn-hangzhou"
   ```

2. **Initialize Terraform**

   Run the following command to initialize the Terraform backend and providers:

   ```bash
   terraform init
   ```

3. **Apply Infrastructure**

   Deploy the infrastructure using:

   ```bash
   terraform apply
   ```

   Confirm with `yes` when prompted.

## Agent-Specific Deployment

To deploy agent-specific configurations, use the `-var` flag with the agent name:

- For Agent A:

  ```bash
  terraform apply -var="agent=agent_a"
  ```

- For Agent B:

  ```bash
  terraform apply -var="agent=agent_b"
  ```

## Available Resources

The harness manages the following resources:

- **ECS Instances**: Compute resources for agent workloads.
- **ApsaraDB for PostgreSQL**: Managed database service.
- **Qdrant Vector Database**: For vector search capabilities.
- **n8n Self-Hosted**: Workflow automation server.

All resources are defined in Terraform modules under `modules/`, ensuring consistency across deployments.

## Environment-Specific Configurations

Environment-specific variables (e.g., `staging`, `prod`) are managed via separate `.tfvars` files. To deploy to a specific environment:

```bash
terraform apply -var-file=env/prod.tfvars
```
