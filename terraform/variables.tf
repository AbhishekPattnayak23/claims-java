# Terraform Variables for Claims Management System
# This file defines all configurable parameters for the infrastructure

# Terraform configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region
}

# Environment Configuration
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

# AWS Configuration
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile name (optional)"
  type        = string
  default     = "default"
}

# Network Configuration
variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

# ECS Configuration
variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "claims-management-cluster"
}

variable "ecs_service_desired_count" {
  description = "Desired number of tasks for each service"
  type = object({
    dev  = number
    prod = number
  })
  default = {
    dev  = 1
    prod = 2
  }
}

# Task Definition Configuration
variable "container_cpu" {
  description = "CPU units for ECS tasks"
  type = object({
    microservices = number
    frontend      = number
  })
  default = {
    microservices = 512  # 0.5 vCPU
    frontend      = 256  # 0.25 vCPU
  }
}

variable "container_memory" {
  description = "Memory allocation for ECS tasks (MB)"
  type = object({
    claims    = number
    auth      = number
    member    = number
    policy    = number
    frontend  = number
  })
  default = {
    claims   = 1024
    auth     = 512
    member   = 1024
    policy   = 1024
    frontend = 512
  }
}

# Docker Image Configuration
variable "docker_image_tags" {
  description = "Docker image tags for each service"
  type = object({
    claims_service   = string
    auth_service     = string
    member_service   = string
    policy_service   = string
    frontend_service = string
  })
  default = {
    claims_service   = "latest"
    auth_service     = "latest"
    member_service   = "latest"
    policy_service   = "latest"
    frontend_service = "latest"
  }
}

variable "ecr_repository_names" {
  description = "ECR repository names for each service"
  type = object({
    claims   = string
    auth     = string
    member   = string
    policy   = string
    frontend = string
  })
  default = {
    claims   = "claims-service"
    auth     = "auth-service"
    member   = "member-service"
    policy   = "policy-service"
    frontend = "frontend"
  }
}

# Database Configuration
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_storage_size" {
  description = "RDS storage size in GB"
  type        = number
  default     = 20
  
  validation {
    condition     = var.rds_storage_size >= 20 && var.rds_storage_size <= 65536
    error_message = "Storage size must be between 20GB and 65536GB"
  }
}

variable "rds_multi_az" {
  description = "Enable multi-AZ deployment for RDS"
  type        = bool
  default     = false
}

variable "database_names" {
  description = "Database names for each microservice"
  type = object({
    claims = string
    member = string
    policy = string
  })
  default = {
    claims = "claimsdb"
    member = "memberdb"
    policy = "policydb"
  }
}

# Security Configuration
variable "jwt_secret" {
  description = "JWT secret key for authentication"
  type        = string
  default     = "your-jwt-secret-key-change-in-production"
  sensitive   = true
}

# Load Balancer Configuration
variable "lb_internal" {
  description = "Whether the load balancer is internal (true) or internet-facing (false)"
  type        = bool
  default     = false
}

variable "lb_health_check_path" {
  description = "Health check path for load balancer"
  type        = string
  default     = "/actuator/health"
}

# Cost Optimization
variable "enable_spot_instances" {
  description = "Enable spot instances for cost savings (dev only)"
  type        = bool
  default     = true
}

variable "autoscaling_enabled" {
  description = "Enable autoscaling for services"
  type        = bool
  default     = false
}

variable "autoscaling_min_capacity" {
  description = "Minimum number of tasks for autoscaling"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum number of tasks for autoscaling"
  type        = number
  default     = 3
}

# Monitoring and Logging
variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
  
  validation {
    condition     = var.log_retention_days >= 1 && var.log_retention_days <= 3653
    error_message = "Log retention must be between 1 and 3653 days"
  }
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "ClaimsManagementSystem"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

# Output Configuration
variable "create_outputs" {
  description = "Whether to create output values"
  type        = bool
  default     = true
}