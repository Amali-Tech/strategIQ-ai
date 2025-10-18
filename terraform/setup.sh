#!/usr/bin/env bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if setup.env file exists
if [ ! -f "setup.env" ]; then
    log_error "setup.env file not found!"
    log_info "Please create a setup.env file with the following variables:"
    cat << 'EOF'
# AWS Configuration
AWS_REGION=eu-west-1
AWS_PROFILE=default

# Project Configuration
PROJECT_NAME=aws-ai-hackathon
ENVIRONMENT=dev

# Backend Configuration
TERRAFORM_STATE_BUCKET=your-terraform-state-bucket
TERRAFORM_STATE_KEY=terraform-state-key
EOF
    exit 1
fi

# Source the setup.env file
log_info "Loading configuration from setup.env..."
source setup.env

# Validate required variables
required_vars=(
    "AWS_REGION"
    "PROJECT_NAME" 
    "ENVIRONMENT"
    "TERRAFORM_STATE_BUCKET"
    "TERRAFORM_STATE_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required variable $var is not set in setup.env"
        exit 1
    fi
done

log_success "Configuration loaded successfully"

# Function to check if AWS CLI is installed and configured
check_aws_cli() {
    log_info "Checking AWS CLI configuration..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Set AWS profile if specified
    if [ -n "$AWS_PROFILE" ] && [ "$AWS_PROFILE" != "default" ]; then
        export AWS_PROFILE="$AWS_PROFILE"
        log_info "Using AWS profile: $AWS_PROFILE"
    fi
    
    # Test AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid"
        log_info "Please run: aws configure"
        exit 1
    fi
    
    log_success "AWS CLI configured correctly"
}

# Function to create S3 bucket for Terraform state
create_terraform_backend() {
    log_info "Setting up Terraform backend..."
    
    # Check if bucket exists
    if aws s3 ls "s3://$TERRAFORM_STATE_BUCKET" >/dev/null 2>&1; then
        log_warning "S3 bucket $TERRAFORM_STATE_BUCKET already exists"
    else
        log_info "Creating S3 bucket: $TERRAFORM_STATE_BUCKET"
        
        if [ "$AWS_REGION" = "us-east-1" ]; then
            aws s3 mb "s3://$TERRAFORM_STATE_BUCKET"
        else
            aws s3 mb "s3://$TERRAFORM_STATE_BUCKET" --region "$AWS_REGION"
        fi
    fi
}

generate_backend_tf() {
    log_info "Generating backend.tf..."
    
    cat > backend.tf << EOF
terraform {
  backend "s3" {
    bucket         = "${TERRAFORM_STATE_BUCKET}"
    key            = "${TERRAFORM_STATE_KEY}"
    region         = "${AWS_REGION}"
    use-lockfile   = true
    encrypt        = true
  }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  
  required_version = ">= 1.0"
}
EOF
    
    log_success "backend.tf generated"
}

# Function to generate terraform.tfvars
generate_tfvars() {
    log_info "Generating terraform.tfvars..."
    
    cat > terraform.tfvars << EOF
# AWS Configuration
aws_region = "${AWS_REGION}"

# Project Configuration
project_name = "${PROJECT_NAME}"
environment  = "${ENVIRONMENT}"
EOF
    
    log_success "terraform.tfvars generated"
}
# Function to generate providers.tf
generate_providers_tf() {
    log_info "Generating providers.tf..."
    
    cat > providers.tf << EOF
provider "aws" {
  region = var.aws_region
  alias  = "primary"
EOF
    
    if [ -n "$AWS_PROFILE" ] && [ "$AWS_PROFILE" != "default" ]; then
        cat >> providers.tf << EOF
  profile = "${AWS_PROFILE}"
EOF
    fi
    
    cat >> providers.tf << EOF
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedBy   = "setup-script"
    }
  }
}
# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}
EOF
    
    log_success "providers.tf generated"
}

# Function to generate root variables.tf
generate_variables_tf() {
    # Populate Variables
    cat > variables.tf << EOF
# project name
variable "project_name" {
    type = string
    description = "The name of this project"
}

# default aws region
variable "aws_region" {
    type = string
    description = "The region in which these resources would be created."
}

# environment
variable "environment" {
    type = string
    description = "could be one of development, production or staging or any other name"
}
EOF
}

# Function to validate generated files
validate_setup() {
    log_info "Validating setup..."
    
    # Check if required files exist
    required_files=("backend.tf" "terraform.tfvars" "providers.tf")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file $file was not created"
            exit 1
        fi
    done
    
    # Test Terraform initialization
    log_info "Testing Terraform initialization..."
    if terraform init -backend=false >/dev/null 2>&1; then
        log_success "Terraform configuration is valid"
    else
        log_error "Terraform configuration validation failed"
        exit 1
    fi
}

create_modules_structure(){
    log_info "Creating modules folder structure..."

    # Define modules array
    modules=(
        "s3"
        "dynamodb" 
        "lambda"
        "agents"
        "api-gateway"
        "iam"
    )

    # Create modules directory
    mkdir -p modules

    for module in "${modules[@]}"; do
        log_info "Creating module: $module"
        
        # Create module directory
        mkdir -p "modules/$module"

        cat > "modules/$module/main.tf" << EOF
# ${module^} Module
# This module manages ${module} resources for the AWS AI Hackathon project

# TODO: Add your ${module} resources here
EOF
        
        # Create variables.tf
        cat > "modules/$module/variables.tf" << EOF
# ${module^} Module Variables

# TODO: Add module-specific variables here
EOF
        
        # Create outputs.tf
        cat > "modules/$module/outputs.tf" << EOF
# ${module^} Module Outputs

# TODO: Add module outputs here
EOF
        
        log_success "Module $module created with main.tf, variables.tf, and outputs.tf"
    done
    log_success "Modules folder structure created successfully"
}

# Function to display next steps
show_next_steps() {
    log_success "Setup completed successfully!"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Review the generated files:"
    echo "   - backend.tf"
    echo "   - terraform.tfvars"
    echo "   - providers.tf"
    echo
    echo "2. Initialize Terraform:"
    echo "   terraform init"
    echo
    echo "3. Plan your infrastructure:"
    echo "   terraform plan"
    echo
    echo "4. Apply your infrastructure:"
    echo "   terraform apply"
    echo -e "${YELLOW}Note:${NC} Make sure to review and customize the generated files as needed."
}

# Main execution
main() {
    log_info "Starting AWS AI Hackathon Terraform setup..."
    
    check_aws_cli
    # create_terraform_backend
    # generate_backend_tf
    # generate_tfvars
    # generate_providers_tf
    # generate_variables_tf
    create_modules_structure
    validate_setup
    show_next_steps
}

# Run main function
main "$@"