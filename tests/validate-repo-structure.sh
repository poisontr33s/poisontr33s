#!/bin/bash

# Repository Structure Validation Script
# This script validates the repository structure and organization

# Note: We don't use set -e here as we want to handle test failures gracefully

# Script configuration
SCRIPT_NAME="validate-repo-structure.sh"
SCRIPT_VERSION="1.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Expected directories
EXPECTED_DIRS=(
    "docs"
    "assets"
    "scripts"
    "src"
    "tests"
)

# Expected files
EXPECTED_FILES=(
    "README.md"
    ".github/copilot-instructions.md"
    "docs/migration_guide.md"
    "scripts/setup-repo-structure.sh"
    "tests/validate-repo-structure.sh"
)

# Validation counters
PASSED_TESTS=0
FAILED_TESTS=0
TOTAL_TESTS=0

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print help
print_help() {
    cat << EOF
${SCRIPT_NAME} v${SCRIPT_VERSION}

DESCRIPTION:
    Validates repository structure and organization.

USAGE:
    ${SCRIPT_NAME} [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -q, --quiet         Suppress all output except errors
    --dirs "dir1 dir2"  Specify custom directories to validate
    --files "file1 file2"  Specify custom files to validate

EXAMPLES:
    ${SCRIPT_NAME}                    # Validate default structure
    ${SCRIPT_NAME} -v                 # Verbose output
    ${SCRIPT_NAME} -q                 # Quiet mode
    ${SCRIPT_NAME} --dirs "docs src"  # Custom directories

EXIT CODES:
    0  - All validations passed
    1  - Some validations failed
    2  - Script error or invalid usage

EOF
}

# Function to run a test
run_test() {
    local test_name=$1
    local test_result=$2
    
    ((TOTAL_TESTS++))
    
    if [[ "$test_result" == "0" ]]; then
        ((PASSED_TESTS++))
        if [[ "$QUIET" != "true" ]]; then
            print_status $GREEN "✓ $test_name"
        fi
    else
        ((FAILED_TESTS++))
        print_status $RED "✗ $test_name"
    fi
}

# Function to validate directories
validate_directories() {
    local dirs=("$@")
    
    if [[ "$QUIET" != "true" ]]; then
        print_status $BLUE "Validating directory structure..."
    fi
    
    for dir in "${dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            run_test "Directory exists: $dir" 0
            
            # Check directory permissions
            if [[ -r "$dir" && -w "$dir" ]]; then
                run_test "Directory accessible: $dir" 0
            else
                run_test "Directory accessible: $dir" 1
            fi
        else
            run_test "Directory exists: $dir" 1
        fi
    done
}

# Function to validate files
validate_files() {
    local files=("$@")
    
    if [[ "$QUIET" != "true" ]]; then
        print_status $BLUE "Validating expected files..."
    fi
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            run_test "File exists: $file" 0
            
            # Check file permissions
            if [[ -r "$file" ]]; then
                run_test "File readable: $file" 0
            else
                run_test "File readable: $file" 1
            fi
        else
            run_test "File exists: $file" 1
        fi
    done
}

# Function to validate executable scripts
validate_scripts() {
    local scripts=(
        "scripts/setup-repo-structure.sh"
    )
    
    if [[ "$QUIET" != "true" ]]; then
        print_status $BLUE "Validating executable scripts..."
    fi
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            if [[ -x "$script" ]]; then
                run_test "Script executable: $script" 0
            else
                run_test "Script executable: $script" 1
            fi
        else
            run_test "Script exists: $script" 1
        fi
    done
}

# Function to validate Git repository
validate_git_repository() {
    if [[ "$QUIET" != "true" ]]; then
        print_status $BLUE "Validating Git repository..."
    fi
    
    if [[ -d ".git" ]]; then
        run_test "Git repository initialized" 0
        
        # Check if we're in the root of the repository
        if [[ "$(git rev-parse --show-toplevel)" == "$(pwd)" ]]; then
            run_test "In repository root directory" 0
        else
            run_test "In repository root directory" 1
        fi
    else
        run_test "Git repository initialized" 1
    fi
}

# Function to validate GitHub configuration
validate_github_config() {
    if [[ "$QUIET" != "true" ]]; then
        print_status $BLUE "Validating GitHub configuration..."
    fi
    
    if [[ -d ".github" ]]; then
        run_test "GitHub configuration directory exists" 0
        
        # Check for important GitHub files
        local github_files=(
            ".github/copilot-instructions.md"
        )
        
        for file in "${github_files[@]}"; do
            if [[ -f "$file" ]]; then
                run_test "GitHub config file: $(basename "$file")" 0
            else
                run_test "GitHub config file: $(basename "$file")" 1
            fi
        done
    else
        run_test "GitHub configuration directory exists" 1
    fi
}

# Function to validate project structure
validate_project_structure() {
    if [[ "$QUIET" != "true" ]]; then
        print_status $BLUE "Validating project structure..."
    fi
    
    # Check if migration guide is in the correct location
    if [[ -f "docs/migration_guide.md" ]]; then
        run_test "Migration guide in docs directory" 0
    else
        run_test "Migration guide in docs directory" 1
    fi
    
    # Check if old migration guide is removed from root
    if [[ ! -f "migration_guide.md" ]]; then
        run_test "Migration guide removed from root" 0
    else
        run_test "Migration guide removed from root" 1
    fi
}

# Function to generate validation report
generate_report() {
    echo
    if [[ "$QUIET" != "true" ]]; then
        print_status $BLUE "Validation Report"
        print_status $BLUE "================"
        print_status $BLUE "Total tests: $TOTAL_TESTS"
        print_status $GREEN "Passed: $PASSED_TESTS"
        print_status $RED "Failed: $FAILED_TESTS"
        
        if [[ $FAILED_TESTS -eq 0 ]]; then
            print_status $GREEN "All validations passed! ✓"
        else
            print_status $RED "Some validations failed! ✗"
        fi
    fi
    
    return $FAILED_TESTS
}

# Function to validate environment
validate_environment() {
    if [[ ! -d ".git" ]]; then
        print_status $RED "Error: Not in a Git repository root directory"
        exit 2
    fi
}

# Main function
main() {
    local dirs=("${EXPECTED_DIRS[@]}")
    local files=("${EXPECTED_FILES[@]}")
    local verbose=false
    local quiet=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                print_help
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -q|--quiet)
                quiet=true
                shift
                ;;
            --dirs)
                if [[ -n "$2" ]]; then
                    IFS=' ' read -ra dirs <<< "$2"
                    shift 2
                else
                    print_status $RED "Error: --dirs requires a space-separated list of directories"
                    exit 2
                fi
                ;;
            --files)
                if [[ -n "$2" ]]; then
                    IFS=' ' read -ra files <<< "$2"
                    shift 2
                else
                    print_status $RED "Error: --files requires a space-separated list of files"
                    exit 2
                fi
                ;;
            *)
                print_status $RED "Error: Unknown option $1"
                print_help
                exit 2
                ;;
        esac
    done
    
    # Set global variables
    VERBOSE=$verbose
    QUIET=$quiet
    
    # Validate environment
    validate_environment
    
    # Display configuration
    if [[ "$verbose" == "true" && "$quiet" != "true" ]]; then
        print_status $BLUE "Repository Structure Validation"
        print_status $BLUE "==============================="
        print_status $BLUE "Script: $SCRIPT_NAME v$SCRIPT_VERSION"
        print_status $BLUE "Working directory: $(pwd)"
        print_status $BLUE "Directories to validate: ${dirs[*]}"
        print_status $BLUE "Files to validate: ${files[*]}"
        echo
    fi
    
    # Run validations
    validate_git_repository
    validate_github_config
    validate_directories "${dirs[@]}"
    validate_files "${files[@]}"
    validate_scripts
    validate_project_structure
    
    # Generate report
    generate_report
    
    # Exit with appropriate code
    if [[ $FAILED_TESTS -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Execute main function
main "$@"