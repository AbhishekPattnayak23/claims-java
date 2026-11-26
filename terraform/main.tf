# Terraform main configuration for Claims Management System
# This file defines the infrastructure resources

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  # Use AWS profile if specified, otherwise use default credentials
  dynamic "profile" {
    for_each = var.aws_profile != "default" ? [1] : []
    content {
      profile = var.aws_profile
    }
  }
}

# Create VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-claims-vpc"
  })
}

# Create public subnets
resource "aws_subnet" "public" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = element(data.aws_availability_zones.available.names, count.index)
  
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${var.environment}-public-subnet-${count.index + 1}"
  })
}

# Create private subnets
resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = element(data.aws_availability_zones.available.names, count.index)
  
  tags = merge(var.tags, {
    Name = "${var.environment}-private-subnet-${count.index + 1}"
  })
}

# Create Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.environment}-igw"
  })
}

# Create route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(var.tags, {
    Name = "${var.environment}-public-rt"
  })
}

# Associate public subnets with public route table
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Create ECS cluster
resource "aws_ecs_cluster" "main" {
  name = var.ecs_cluster_name
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = var.tags
}

# Create ECR repositories for each service
resource "aws_ecr_repository" "services" {
  for_each = var.ecr_repository_names
  
  name                 = each.value
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = var.tags
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Outputs
output "vpc_id" {
  value = aws_vpc.main.id
  description = "VPC ID"
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
  description = "ECS Cluster Name"
}

output "ecr_repository_urls" {
  value = {
    for service, repo in aws_ecr_repository.services : service => repo.repository_url
  }
  description = "ECR Repository URLs"
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
  description = "Public Subnet IDs"
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
  description = "Private Subnet IDs"
}