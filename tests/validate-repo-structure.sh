#!/bin/bash

# Repository Structure Validation Test
# Tests the automated folder structure setup functionality

set -e

# Test configuration
TEST_DIR="/tmp/repo-structure-test-$(date +%s)"
SCRIPT_PATH="$(pwd)/scripts/setup-repo-structure.sh"
REQUIRED_FOLDERS=("docs" "assets" "scripts" "src" "tests")
TEST_RESULTS=()

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    TEST_RESULTS+=("PASS: $1")
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    TEST_RESULTS+=("FAIL: $1")
}

# Test functions
test_script_exists() {
    log_info "Testing if setup script exists..."
    if [ -f "$SCRIPT_PATH" ]; then
        log_success "Setup script exists at $SCRIPT_PATH"
        return 0
    else
        log_error "Setup script not found at $SCRIPT_PATH"
        return 1
    fi
}

test_script_executable() {
    log_info "Testing if setup script is executable..."
    if [ -x "$SCRIPT_PATH" ]; then
        log_success "Setup script is executable"
        return 0
    else
        log_error "Setup script is not executable"
        return 1
    fi
}

setup_test_environment() {
    log_info "Setting up test environment at $TEST_DIR..."
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"
    
    # Initialize git repo
    git init -q
    git config user.email "test@example.com"
    git config user.name "Test User"
    
    # Copy setup script
    cp "$SCRIPT_PATH" "./setup-repo-structure.sh"
    chmod +x "./setup-repo-structure.sh"
    
    log_success "Test environment ready"
}

test_folder_creation() {
    log_info "Testing folder structure creation..."
    
    # Run the setup script
    if ./setup-repo-structure.sh > /dev/null 2>&1; then
        log_success "Setup script executed successfully"
    else
        log_error "Setup script execution failed"
        return 1
    fi
    
    # Check each required folder
    local all_folders_exist=true
    for folder in "${REQUIRED_FOLDERS[@]}"; do
        if [ -d "$folder" ]; then
            log_success "Folder '$folder' created successfully"
        else
            log_error "Folder '$folder' not created"
            all_folders_exist=false
        fi
    done
    
    if $all_folders_exist; then
        log_success "All required folders created"
        return 0
    else
        log_error "Some folders missing"
        return 1
    fi
}

test_gitkeep_files() {
    log_info "Testing .gitkeep file creation..."
    
    local all_gitkeep_exist=true
    for folder in "${REQUIRED_FOLDERS[@]}"; do
        if [ -f "$folder/.gitkeep" ]; then
            log_success ".gitkeep file exists in '$folder'"
        else
            log_error ".gitkeep file missing in '$folder'"
            all_gitkeep_exist=false
        fi
    done
    
    if $all_gitkeep_exist; then
        log_success "All .gitkeep files created"
        return 0
    else
        log_error "Some .gitkeep files missing"
        return 1
    fi
}

test_migration_guide_creation() {
    log_info "Testing migration guide template creation..."
    
    if [ -f "docs/migration_guide.md" ]; then
        log_success "Migration guide template created in docs/"
        
        # Check if it has content
        if [ -s "docs/migration_guide.md" ]; then
            log_success "Migration guide template has content"
            
            # Check for key sections
            if grep -q "# Migration Guide Template" "docs/migration_guide.md"; then
                log_success "Migration guide has proper title"
            else
                log_error "Migration guide missing proper title"
                return 1
            fi
            
            if grep -q "## Table of Contents" "docs/migration_guide.md"; then
                log_success "Migration guide has table of contents"
            else
                log_error "Migration guide missing table of contents"
                return 1
            fi
            
        else
            log_error "Migration guide template is empty"
            return 1
        fi
    else
        log_error "Migration guide template not created"
        return 1
    fi
}

test_existing_migration_guide() {
    log_info "Testing existing migration guide handling..."
    
    # Create a test migration guide in root
    echo "# Test Migration Guide" > migration_guide.md
    echo "This is a test migration guide." >> migration_guide.md
    
    # Run setup script again
    if ./setup-repo-structure.sh > /dev/null 2>&1; then
        log_success "Setup script handled existing migration guide"
        
        # Check if original guide still exists in docs
        if [ -f "docs/migration_guide.md" ]; then
            log_success "Migration guide exists in docs/"
        else
            log_error "Migration guide not found in docs/ after re-run"
            return 1
        fi
        
        # Check if root migration guide was handled
        if [ ! -f "migration_guide.md" ]; then
            log_success "Root migration guide properly handled"
        else
            log_warning "Root migration guide still exists"
        fi
        
    else
        log_error "Setup script failed with existing migration guide"
        return 1
    fi
}

test_idempotency() {
    log_info "Testing script idempotency (multiple runs)..."
    
    # Run script multiple times
    for i in {1..3}; do
        if ./setup-repo-structure.sh > /dev/null 2>&1; then
            log_success "Idempotency test run $i successful"
        else
            log_error "Idempotency test run $i failed"
            return 1
        fi
    done
    
    # Verify structure still intact
    for folder in "${REQUIRED_FOLDERS[@]}"; do
        if [ ! -d "$folder" ]; then
            log_error "Folder '$folder' missing after multiple runs"
            return 1
        fi
    done
    
    log_success "Script is idempotent"
}

cleanup_test_environment() {
    log_info "Cleaning up test environment..."
    cd /
    rm -rf "$TEST_DIR"
    log_success "Test environment cleaned up"
}

print_test_summary() {
    echo ""
    echo "=========================================="
    echo "           TEST SUMMARY"
    echo "=========================================="
    
    local pass_count=0
    local fail_count=0
    
    for result in "${TEST_RESULTS[@]}"; do
        if [[ $result == PASS* ]]; then
            echo -e "${GREEN}$result${NC}"
            ((pass_count++))
        else
            echo -e "${RED}$result${NC}"
            ((fail_count++))
        fi
    done
    
    echo ""
    echo "Tests Passed: $pass_count"
    echo "Tests Failed: $fail_count"
    echo "Total Tests: $((pass_count + fail_count))"
    
    if [ $fail_count -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
        return 0
    else
        echo -e "${RED}💥 SOME TESTS FAILED!${NC}"
        return 1
    fi
}

# Main test execution
main() {
    echo "🧪 Repository Structure Validation Test"
    echo "========================================"
    echo ""
    
    # Pre-flight checks
    test_script_exists || exit 1
    test_script_executable || exit 1
    
    # Set up test environment
    setup_test_environment
    
    # Run tests
    test_folder_creation
    test_gitkeep_files  
    test_migration_guide_creation
    test_existing_migration_guide
    test_idempotency
    
    # Cleanup
    cleanup_test_environment
    
    # Summary
    print_test_summary
}

# Execute main function
main "$@"