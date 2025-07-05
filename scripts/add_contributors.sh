#!/bin/bash

# GitHub Contributor Automation - Shell Wrapper
# This script provides a simplified interface for adding contributors

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
CONFIG_FILE="$PROJECT_DIR/config/contributor-config.json"
PYTHON_SCRIPT="$PROJECT_DIR/scripts/add_contributors.py"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to display help
show_help() {
    cat << EOF
GitHub Contributor Automation - Shell Wrapper

Usage: $0 [OPTIONS]

Options:
    -u, --username USERNAME      GitHub username to add
    -e, --email EMAIL           Email address to add
    -p, --permission PERMISSION Permission level (pull, push, admin, maintain, triage)
    -r, --repository REPO       Repository in format owner/repo
    -t, --token TOKEN           GitHub token
    -b, --batch FILE            Batch file with multiple contributors
    -c, --config FILE           Configuration file path
    -h, --help                  Show this help message

Environment Variables:
    GITHUB_TOKEN                GitHub token
    GITHUB_REPOSITORY           Repository in format owner/repo

Examples:
    $0 --username johndoe --permission pull
    $0 --email user@example.com --permission push
    $0 --batch examples/batch-contributors.json

EOF
}

# Function to check prerequisites
check_prerequisites() {
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check if PyGithub is installed
    if ! python3 -c "import github" &> /dev/null; then
        print_error "PyGithub is required but not installed."
        print_status "Install with: pip install PyGithub"
        exit 1
    fi
    
    # Check if script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        exit 1
    fi
    
    # Check if config exists
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
}

# Parse command line arguments
USERNAME=""
EMAIL=""
PERMISSION=""
REPOSITORY=""
TOKEN=""
BATCH_FILE=""
CUSTOM_CONFIG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            USERNAME="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -p|--permission)
            PERMISSION="$2"
            shift 2
            ;;
        -r|--repository)
            REPOSITORY="$2"
            shift 2
            ;;
        -t|--token)
            TOKEN="$2"
            shift 2
            ;;
        -b|--batch)
            BATCH_FILE="$2"
            shift 2
            ;;
        -c|--config)
            CUSTOM_CONFIG="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check prerequisites
check_prerequisites

# Use custom config if provided
if [[ -n "$CUSTOM_CONFIG" ]]; then
    CONFIG_FILE="$CUSTOM_CONFIG"
fi

# Get token from environment if not provided
if [[ -z "$TOKEN" ]]; then
    TOKEN="$GITHUB_TOKEN"
fi

# Get repository from environment if not provided
if [[ -z "$REPOSITORY" ]]; then
    REPOSITORY="$GITHUB_REPOSITORY"
fi

# Validate required parameters
if [[ -z "$TOKEN" ]]; then
    print_error "GitHub token is required. Use --token or set GITHUB_TOKEN environment variable."
    exit 1
fi

if [[ -z "$REPOSITORY" ]]; then
    print_error "Repository is required. Use --repository or set GITHUB_REPOSITORY environment variable."
    exit 1
fi

# Build Python command
PYTHON_CMD="python3 $PYTHON_SCRIPT"
PYTHON_CMD="$PYTHON_CMD --repository $REPOSITORY"
PYTHON_CMD="$PYTHON_CMD --token $TOKEN"
PYTHON_CMD="$PYTHON_CMD --config-file $CONFIG_FILE"

if [[ -n "$BATCH_FILE" ]]; then
    # Batch mode
    if [[ ! -f "$BATCH_FILE" ]]; then
        print_error "Batch file not found: $BATCH_FILE"
        exit 1
    fi
    
    print_status "Processing batch file: $BATCH_FILE"
    PYTHON_CMD="$PYTHON_CMD --batch-file $BATCH_FILE"
    
elif [[ -n "$USERNAME" ]]; then
    # Username mode
    print_status "Adding contributor by username: $USERNAME"
    PYTHON_CMD="$PYTHON_CMD --username $USERNAME"
    
    if [[ -n "$PERMISSION" ]]; then
        PYTHON_CMD="$PYTHON_CMD --permission $PERMISSION"
    fi
    
elif [[ -n "$EMAIL" ]]; then
    # Email mode
    print_status "Adding contributor by email: $EMAIL"
    PYTHON_CMD="$PYTHON_CMD --email $EMAIL"
    
    if [[ -n "$PERMISSION" ]]; then
        PYTHON_CMD="$PYTHON_CMD --permission $PERMISSION"
    fi
    
else
    print_error "Either --username, --email, or --batch must be provided."
    show_help
    exit 1
fi

# Execute the Python script
print_status "Executing: $PYTHON_CMD"
if eval "$PYTHON_CMD"; then
    print_status "Operation completed successfully!"
else
    print_error "Operation failed. Check logs for details."
    exit 1
fi