#!/bin/bash
set -e

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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/terraform"

log_info "=== AWS AI Hackathon Infrastructure Deployment Verification ==="
log_info "Script directory: $SCRIPT_DIR"
log_info "Terraform directory: $TERRAFORM_DIR"

# Check if we're in the right directory
if [[ ! -f "$TERRAFORM_DIR/main.tf" ]]; then
    log_error "terraform/main.tf not found. Please run this script from the project root."
    exit 1
fi

cd "$TERRAFORM_DIR"

# Check if terraform.tfvars exists
if [[ ! -f "terraform.tfvars" ]]; then
    log_warning "terraform.tfvars not found. Please copy terraform.tfvars.example to terraform.tfvars and update values."
    if [[ -f "terraform.tfvars.example" ]]; then
        log_info "Copying terraform.tfvars.example to terraform.tfvars..."
        cp terraform.tfvars.example terraform.tfvars
        log_warning "Please edit terraform.tfvars and add your YouTube API key before proceeding."
        exit 1
    else
        log_error "terraform.tfvars.example not found either. Please check your setup."
        exit 1
    fi
fi

# Check if YouTube API key is set
if grep -q "YOUR_YOUTUBE_API_KEY_HERE" terraform.tfvars; then
    log_error "Please replace YOUR_YOUTUBE_API_KEY_HERE with your actual YouTube API key in terraform.tfvars"
    exit 1
fi

# Check if AWS credentials are configured
log_info "Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    log_error "AWS credentials not configured. Please run 'aws configure' or set AWS environment variables."
    exit 1
fi

log_success "AWS credentials configured"

# Check if Python dependencies are ready
log_info "Checking Python dependencies..."
if [[ ! -d "../python" ]] || [[ -z "$(ls -A ../python 2>/dev/null)" ]]; then
    log_warning "Python dependencies not found. Running sync-python-deps.sh..."
    if [[ -f "../sync-python-deps.sh" ]]; then
        cd ..
        chmod +x sync-python-deps.sh
        ./sync-python-deps.sh
        cd "$TERRAFORM_DIR"
        log_success "Python dependencies synced"
    else
        log_error "sync-python-deps.sh not found. Please ensure Python dependencies are installed."
        exit 1
    fi
else
    log_success "Python dependencies found"
fi

# Initialize Terraform
log_info "Initializing Terraform..."
if terraform init; then
    log_success "Terraform initialized successfully"
else
    log_error "Terraform initialization failed"
    exit 1
fi

# Validate Terraform configuration
log_info "Validating Terraform configuration..."
if terraform validate; then
    log_success "Terraform configuration is valid"
else
    log_error "Terraform configuration validation failed"
    exit 1
fi

# Plan Terraform deployment
log_info "Planning Terraform deployment..."
if terraform plan -out=tfplan; then
    log_success "Terraform plan completed successfully"
    log_info "Plan saved to tfplan file"
else
    log_error "Terraform planning failed"
    exit 1
fi

# Ask user if they want to apply
echo ""
log_info "Terraform plan completed successfully!"
log_warning "This will create AWS resources that may incur costs."
read -p "Do you want to apply the Terraform plan? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Applying Terraform plan..."
    if terraform apply tfplan; then
        log_success "Terraform deployment completed successfully!"
        
        # Display important outputs
        echo ""
        log_info "=== Important Endpoints ==="
        if terraform output -raw upload_endpoint > /dev/null 2>&1; then
            echo "Upload Endpoint: $(terraform output -raw upload_endpoint)"
        fi
        if terraform output -raw status_endpoint > /dev/null 2>&1; then
            echo "Status Endpoint: $(terraform output -raw status_endpoint)"
        fi
        if terraform output -raw s3_bucket_name > /dev/null 2>&1; then
            echo "S3 Bucket: $(terraform output -raw s3_bucket_name)"
        fi
        
        echo ""
        log_success "Infrastructure deployment verification completed!"
        log_info "You can now test the image upload pipeline using the endpoints above."
        
    else
        log_error "Terraform deployment failed"
        exit 1
    fi
else
    log_info "Terraform apply cancelled by user"
    log_info "You can apply the plan later by running: terraform apply tfplan"
fi

# Cleanup
rm -f tfplan