# Deployment Guide for Claims Management System

This document provides instructions for deploying the Claims Management System using Terraform infrastructure as code.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Terraform Configuration](#terraform-configuration)
3. [Environment Variables](#environment-variables)
4. [Deployment Steps](#deployment-steps)
5. [Variables Reference](#variables-reference)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the system, ensure you have the following:

- **AWS Account** with appropriate IAM permissions
- **AWS CLI** installed and configured (`aws configure`)
- **Terraform** (version >= 1.0.0) installed
- **Docker** installed (for local development)
- **Git** for version control

### AWS IAM Permissions Required
- AmazonEC2FullAccess
- AmazonECS_FullAccess  
- AmazonRDSFullAccess
- AmazonVPCFullAccess
- IAMFullAccess
- CloudWatchLogsFullAccess

## Terraform Configuration

The Terraform configuration is organized in the `/workspace/terraform/` directory:

```
terraform/
├── main.tf           # Main infrastructure configuration
├── variables.tf      # Input variables (YOU ARE HERE)
├── outputs.tf        # Output values
└── modules/         # Reusable modules (optional)
```

### Working with Terraform Variables

Terraform variables are defined in `variables.tf` and can be set in several ways:

#### 1. Using Variable Definition Files (.tfvars)

Create a `terraform.tfvars` file in the terraform directory:

```hcl
# terraform.tfvars
environment        = "dev"
aws_region         = "us-east-1"
vpc_cidr           = "10.0.0.0/16"
ecs_task_cpu       = 512
ecs_task_memory    = 1024
db_instance_class  = "db.t3.micro"
docker_image_tag   = "latest"
```

Apply with:
```bash
terraform apply -var-file="terraform.tfvars"
```

#### 2. Using Environment Variables

Prefix Terraform variables with `TF_VAR_`:

```bash
export TF_VAR_environment="dev"
export TF_VAR_aws_region="us-east-1"
export TF_VAR_docker_image_tag="v1.0.0"
terraform apply
```

#### 3. Command-line Flags

```bash
terraform apply \
  -var="environment=prod" \
  -var="aws_region=us-west-2" \
  -var="docker_image_tag=latest"
```

#### 4. Interactive Prompt

If no value is provided, Terraform will prompt for each variable:
```bash
terraform apply
```

## Environment Variables

### Required Environment Variables

Copy the template file and configure your environment:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Database Configuration
DB_URL=jdbc:postgresql://postgres:5432/claimsdb
DB_USER=postgres
DB_PASSWORD=postgres

# JWT Configuration
JWT_SECRET=your-256-bit-secret-key-change-in-production
JWT_EXPIRATION=86400000

# Service Ports
CLAIMS_SERVICE_PORT=8081
AUTH_SERVICE_PORT=8080
MEMBER_SERVICE_PORT=8082

# Cloud Configuration
AWS_REGION=us-east-1
ECS_CLUSTER_NAME=claims-management-cluster
ECR_REGISTRY=<aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### Mapping Environment Variables to Terraform

Some environment variables directly correspond to Terraform variables:

| Environment Variable | Terraform Variable | Default Value |
|----------------------|-------------------|---------------|
| AWS_REGION           | `aws_region`      | "us-east-1"   |
| ECS_CLUSTER_NAME     | `ecs_cluster_name`| "claims-management-cluster" |
| Docker Image Tags    | `docker_image_tag`| "latest"      |

## Deployment Steps

### Step 1: Initialize Terraform

```bash
cd /workspace/terraform
terraform init
```

### Step 2: Review the Plan

```bash
# Review what will be created
terraform plan

# Review with specific variable values
terraform plan -var="environment=dev" -var="aws_region=us-east-1"
```

### Step 3: Apply the Configuration

```bash
# Apply with default variables
terraform apply -auto-approve

# Or apply with custom variables
terraform apply \
  -var="environment=prod" \
  -var="aws_region=us-west-2" \
  -var="db_instance_class=db.t3.medium" \
  -auto-approve
```

### Step 4: Verify Deployment

```bash
# View outputs
terraform output

# Check ECS cluster status
aws ecs list-clusters --region $(terraform output -raw aws_region)

# Check RDS instance status
aws rds describe-db-instances \
  --region $(terraform output -raw aws_region) \
  --query "DBInstances[?DBInstanceIdentifier=='claims-db-$(terraform output -raw environment)']"
```

### Step 5: Update and Re-deploy

When making changes to your infrastructure:

```bash
# Update the plan
terraform plan -out=plan.tfplan

# Apply the changes
terraform apply plan.tfplan
```

## Variables Reference

### Core Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `environment` | Deployment environment (dev/staging/prod) | `"dev"` | Yes |
| `aws_region` | AWS region to deploy resources | `"us-east-1"` | Yes |
| `vpc_cidr` | CIDR block for VPC | `"10.0.0.0/16"` | Yes |
| `public_subnet_cidrs` | CIDR blocks for public subnets | `["10.0.1.0/24", "10.0.2.0/24"]` | Yes |
| `private_subnet_cidrs` | CIDR blocks for private subnets | `["10.0.10.0/24", "10.0.20.0/24"]` | Yes |

### ECS Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ecs_cluster_name` | Name of the ECS cluster | `"claims-management"` | Yes |
| `ecs_task_cpu` | CPU units for ECS tasks | `512` | Yes |
| `ecs_task_memory` | Memory (MiB) for ECS tasks | `1024` | Yes |
| `desired_count` | Number of tasks to run | `2` | Yes |
| `docker_image_tag` | Docker image tag for containers | `"latest"` | Yes |

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `db_instance_class` | RDS instance class | `"db.t3.micro"` | Yes |
| `db_allocated_storage` | Storage allocated to DB (GB) | `20` | Yes |
| `db_engine` | Database engine | `"postgres"` | Yes |
| `db_engine_version` | Database engine version | `"14.7"` | Yes |
| `db_name` | Name of the default database | `"claimsdb"` | Yes |
| `db_username` | Database username | `"postgres"` | Yes |
| `db_password` | Database password | *Must be provided* | Yes |

### Networking

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `availability_zones` | Availability zones to use | `["us-east-1a", "us-east-1b"]` | Yes |
| `enable_nat_gateway` | Enable NAT gateway for private subnets | `true` | No |
| `single_nat_gateway` | Use single NAT gateway for all AZs | `true` | No |

## Environment-Specific Configuration

### Development Environment

```hcl
# dev.tfvars
environment        = "dev"
aws_region         = "us-east-1"
ecs_task_cpu       = 256
ecs_task_memory    = 512
db_instance_class  = "db.t3.micro"
desired_count      = 1
docker_image_tag   = "dev-latest"
```

Apply with:
```bash
terraform apply -var-file="dev.tfvars"
```

### Production Environment

```hcl
# prod.tfvars
environment        = "prod"
aws_region         = "us-west-2"
ecs_task_cpu       = 1024
ecs_task_memory    = 2048
db_instance_class  = "db.t3.medium"
desired_count      = 3
docker_image_tag   = "v1.0.0"
enable_backup      = true
backup_retention_period = 30
```

Apply with:
```bash
terraform apply -var-file="prod.tfvars"
```

## Using Terraform Outputs

After deployment, Terraform outputs useful information:

```bash
# View all outputs
terraform output

# Get specific outputs
terraform output -raw ecs_cluster_name
terraform output -raw rds_endpoint
terraform output -json load_balancer_dns
```

Common outputs include:
- `ecs_cluster_name`: Name of the created ECS cluster
- `rds_endpoint`: RDS database endpoint
- `load_balancer_dns`: Application Load Balancer DNS name
- `vpc_id`: ID of the created VPC

## Best Practices

### 1. Version Control for Variables

```bash
# Never commit sensitive data
echo "*.tfvars" >> .gitignore
echo "terraform.tfstate*" >> .gitignore
echo ".terraform/" >> .gitignore
```

### 2. Use Separate Workspaces

```bash
# Create workspace for each environment
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch between workspaces
terraform workspace select dev
```

### 3. Store Sensitive Data Securely

```bash
# Use AWS Secrets Manager or Parameter Store
# Or use Terraform Cloud/Enterprise for state management
```

### 4. Regular State Backups

```bash
# Backup your state file regularly
terraform state pull > terraform.tfstate.backup
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Verify AWS credentials
   aws sts get-caller-identity
   
   # Configure AWS CLI
   aws configure
   ```

2. **State Lock Issues**
   ```bash
   # If terraform gets stuck
   terraform force-unlock <LOCK_ID>
   ```

3. **Resource Creation Failures**
   ```bash
   # Check cloud formation events
   terraform refresh
   terraform show
   ```

4. **Variable Not Set**
   ```bash
   # List all required variables
   terraform plan 2>&1 | grep -A5 "Error:"
   ```

### Debugging

```bash
# Enable verbose logging
export TF_LOG=DEBUG
terraform plan

# Check provider versions
terraform version
terraform providers
```

## Next Steps

1. **Set up CI/CD Pipeline** - Automate deployments with GitHub Actions
2. **Implement Monitoring** - Add CloudWatch alarms and dashboards
3. **Security Hardening** - Implement security groups and IAM roles
4. **Cost Optimization** - Set up budget alerts and cost analysis

## Support

For issues with Terraform deployment:
1. Check the [Terraform documentation](https://www.terraform.io/docs)
2. Review AWS service limits and quotas
3. Check IAM permissions
4. Review Terraform state file for inconsistencies

---

*Last Updated: $(date)*
*Version: 1.0.0*