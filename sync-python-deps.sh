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

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
PYTHON_DIR="$PROJECT_ROOT/python"
VENV_DIR="$PROJECT_ROOT/venv"
MAX_RETRIES=3

# Default requirements if file doesn't exist
DEFAULT_REQUIREMENTS="google-api-python-client
google-auth-oauthlib
google-auth-httplib2
dotenv
isodate
boto3
botocore"

# Check if requirements.txt exists and is not empty
check_requirements_file() {
    log_info "Checking requirements.txt file..."
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_warning "requirements.txt not found at project root"
        return 1
    fi
    
    if [[ ! -s "$REQUIREMENTS_FILE" ]]; then
        log_warning "requirements.txt exists but is empty"
        return 1
    fi
    
    log_success "requirements.txt found and contains content"
    return 0
}

# Create requirements.txt with default dependencies
create_requirements_file() {
    log_info "Creating requirements.txt with default dependencies..."
    
    echo "$DEFAULT_REQUIREMENTS" > "$REQUIREMENTS_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_success "Created requirements.txt with default dependencies"
        return 0
    else
        log_error "Failed to create requirements.txt"
        return 1
    fi
}

# Check if virtual environment is activated
check_venv() {
    log_info "Checking virtual environment..."
    
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log_warning "Virtual environment not activated"
        return 1
    fi
    
    log_success "Virtual environment is activated: $VIRTUAL_ENV"
    return 0
}

# Create and activate virtual environment
setup_venv() {
    log_info "Setting up virtual environment..."
    
    # Create venv if it doesn't exist
    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "Creating virtual environment at $VENV_DIR"
        python3 -m venv "$VENV_DIR"
        
        if [[ $? -ne 0 ]]; then
            log_error "Failed to create virtual environment"
            return 1
        fi
    fi
    
    # Activate venv
    log_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    if [[ $? -eq 0 ]]; then
        log_success "Virtual environment activated"
        # Update pip to latest version
        pip install --upgrade pip > /dev/null 2>&1
        return 0
    else
        log_error "Failed to activate virtual environment"
        return 1
    fi
}

# Check if python directory exists
check_python_dir() {
    log_info "Checking python directory..."
    
    if [[ ! -d "$PYTHON_DIR" ]]; then
        log_warning "Python directory not found at project root"
        return 1
    fi
    
    log_success "Python directory found"
    return 0
}

# Create python directory
create_python_dir() {
    log_info "Creating python directory..."
    
    mkdir -p "$PYTHON_DIR"
    
    if [[ $? -eq 0 ]]; then
        log_success "Python directory created at $PYTHON_DIR"
        return 0
    else
        log_error "Failed to create python directory"
        return 1
    fi
}

# Install dependencies with retry mechanism
install_dependencies() {
    local attempt=1
    
    log_info "Installing dependencies to python directory..."
    
    while [[ $attempt -le $MAX_RETRIES ]]; do
        log_info "Installation attempt $attempt of $MAX_RETRIES..."
        
        # Clean python directory for fresh install
        if [[ -d "$PYTHON_DIR" ]]; then
            rm -rf "$PYTHON_DIR"/*
        fi
        
        # Install dependencies with progress visible
        log_info "Downloading and installing packages..."
        echo -e "${BLUE}[PROGRESS]${NC} Installing packages (this may take a moment)..."
        
        if pip install -r "$REQUIREMENTS_FILE" -t "$PYTHON_DIR" --progress-bar on --disable-pip-version-check 2>&1 | while IFS= read -r line; do
            # Show download progress and package names
            if [[ "$line" =~ "Downloading" ]] || [[ "$line" =~ "Installing" ]] || [[ "$line" =~ "Successfully installed" ]]; then
                echo -e "${BLUE}[PROGRESS]${NC} $line"
            elif [[ "$line" =~ "ERROR" ]] || [[ "$line" =~ "error" ]]; then
                echo -e "${RED}[ERROR]${NC} $line" >&2
            fi
        done; then
            log_success "Dependencies installed successfully"
            return 0
        else
            log_warning "Installation attempt $attempt failed"
            
            if [[ $attempt -eq $MAX_RETRIES ]]; then
                log_error "Failed to install dependencies after $MAX_RETRIES attempts"
                return 1
            fi
            
            # Wait before retry
            log_info "Waiting 3 seconds before retry..."
            sleep 3
            ((attempt++))
        fi
    done
}

# Validate installation
validate_installation() {
    log_info "Validating installation..."
    
    # Check if python directory has content
    if [[ ! "$(ls -A $PYTHON_DIR 2>/dev/null)" ]]; then
        log_error "Python directory is empty after installation"
        return 1
    fi
    
    # Count installed packages
    local package_count=$(find "$PYTHON_DIR" -maxdepth 1 -type d | wc -l)
    log_success "Installation validated: $((package_count - 1)) packages installed"
    
    return 0
}

# Main execution
main() {
    log_info "Starting Python dependencies sync..."
    log_info "Project root: $PROJECT_ROOT"
    
    # Check and setup requirements file
    if ! check_requirements_file; then
        if ! create_requirements_file; then
            log_error "Cannot proceed without requirements.txt"
            exit 1
        fi
    fi
    
    # Check and setup virtual environment
    if ! check_venv; then
        if ! setup_venv; then
            log_error "Cannot proceed without virtual environment"
            exit 1
        fi
    fi
    
    # Check and setup python directory
    if ! check_python_dir; then
        if ! create_python_dir; then
            log_error "Cannot proceed without python directory"
            exit 1
        fi
    fi
    
    # Install dependencies
    if ! install_dependencies; then
        log_error "Failed to install dependencies"
        exit 1
    fi
    
    # Validate installation
    if ! validate_installation; then
        log_error "Installation validation failed"
        exit 1
    fi
    
    log_success "Python dependencies sync completed successfully!"
    log_info "Dependencies are ready for Lambda layer packaging"
}

# Cleanup function for graceful exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        log_error "Script failed. Check the logs above for details."
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"