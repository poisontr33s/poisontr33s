#!/bin/bash

# Post-Merge Validation Script for Issue #2
# Validates integration and cleanup after PR merge

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MERGED_BRANCH="copilot/fix-71a13388-9183-473b-a4d1-dadd0595d643"
MAIN_BRANCH="main"
PR_NUMBER="2"

echo -e "${BLUE}🔍 Post-Merge Validation for Issue #2${NC}"
echo -e "${BLUE}======================================${NC}"

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS:${NC} $message"
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL:${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN:${NC} $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO:${NC} $message"
            ;;
    esac
}

# Function to check if branch exists locally
check_local_branch() {
    local branch_name=$1
    if git branch --list "$branch_name" | grep -q "$branch_name"; then
        return 0
    else
        return 1
    fi
}

# Function to check if branch exists on remote
check_remote_branch() {
    local branch_name=$1
    if git ls-remote --heads origin "$branch_name" | grep -q "$branch_name"; then
        return 0
    else
        return 1
    fi
}

# Function to validate merge integration
validate_merge_integration() {
    print_status "INFO" "Validating merge integration..."
    
    # Check if we're on the correct branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$current_branch" != "$MAIN_BRANCH" ]; then
        print_status "WARN" "Not on main branch. Current: $current_branch"
        return 1
    fi
    
    # Check if merge commit exists (try multiple patterns)
    local merge_patterns=("Merge pull request #$PR_NUMBER" "pull request #$PR_NUMBER" "#$PR_NUMBER")
    local merge_found=false
    
    for pattern in "${merge_patterns[@]}"; do
        if git log --all --oneline --grep="$pattern" | grep -q "$pattern"; then
            print_status "PASS" "Merge reference for PR #$PR_NUMBER found in history"
            merge_found=true
            break
        fi
    done
    
    if [ "$merge_found" = false ]; then
        # In shallow clones, we may not have complete history
        if [ -f ".git/shallow" ]; then
            print_status "WARN" "Shallow clone detected - merge history may be incomplete"
            # Check if the branch content exists instead
            if [ -f "README.md" ] && [ -f "migration_guide.md" ]; then
                print_status "PASS" "Expected repository structure exists (merge likely successful)"
                return 0
            else
                print_status "FAIL" "Expected repository structure missing"
                return 1
            fi
        else
            print_status "FAIL" "Merge commit for PR #$PR_NUMBER not found"
            return 1
        fi
    fi
    
    return 0
}

# Function to validate branch cleanup
validate_branch_cleanup() {
    print_status "INFO" "Validating branch cleanup..."
    
    local cleanup_issues=0
    
    # Check local branch existence
    if check_local_branch "$MERGED_BRANCH"; then
        print_status "WARN" "Local branch '$MERGED_BRANCH' still exists"
        cleanup_issues=$((cleanup_issues + 1))
    else
        print_status "PASS" "Local branch '$MERGED_BRANCH' has been deleted"
    fi
    
    # Check remote branch existence
    if check_remote_branch "$MERGED_BRANCH"; then
        print_status "WARN" "Remote branch '$MERGED_BRANCH' still exists"
        cleanup_issues=$((cleanup_issues + 1))
    else
        print_status "PASS" "Remote branch '$MERGED_BRANCH' has been deleted"
    fi
    
    return $cleanup_issues
}

# Function to validate repository structure
validate_repository_structure() {
    print_status "INFO" "Validating repository structure..."
    
    local expected_files=("README.md" "migration_guide.md")
    local structure_issues=0
    
    for file in "${expected_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "PASS" "Required file '$file' exists"
        else
            print_status "FAIL" "Required file '$file' missing"
            structure_issues=$((structure_issues + 1))
        fi
    done
    
    # Check if .github directory exists
    if [ -d ".github" ]; then
        print_status "PASS" "GitHub configuration directory exists"
    else
        print_status "FAIL" "GitHub configuration directory missing"
        structure_issues=$((structure_issues + 1))
    fi
    
    return $structure_issues
}

# Function to check for residual merge issues
check_residual_issues() {
    print_status "INFO" "Checking for residual merge issues..."
    
    local issues=0
    
    # Check for merge conflict markers
    if grep -r "<<<<<<< \|======= \|>>>>>>> " . --exclude-dir=.git 2>/dev/null; then
        print_status "FAIL" "Merge conflict markers found in repository"
        issues=$((issues + 1))
    else
        print_status "PASS" "No merge conflict markers found"
    fi
    
    # Check for temporary files
    if find . -name "*.orig" -o -name "*.rej" -o -name "*~" 2>/dev/null | grep -q .; then
        print_status "WARN" "Temporary files found in repository"
        issues=$((issues + 1))
    else
        print_status "PASS" "No temporary files found"
    fi
    
    return $issues
}

# Function to validate working tree
validate_working_tree() {
    print_status "INFO" "Validating working tree status..."
    
    if [ -z "$(git status --porcelain)" ]; then
        print_status "PASS" "Working tree is clean"
        return 0
    else
        print_status "WARN" "Working tree has uncommitted changes"
        git status --short
        return 1
    fi
}

# Function to generate cleanup recommendations
generate_cleanup_recommendations() {
    print_status "INFO" "Generating cleanup recommendations..."
    
    echo -e "\n${YELLOW}🔧 Cleanup Recommendations:${NC}"
    
    if check_local_branch "$MERGED_BRANCH"; then
        echo -e "  • Delete local branch: ${BLUE}git branch -d $MERGED_BRANCH${NC}"
    fi
    
    if check_remote_branch "$MERGED_BRANCH"; then
        echo -e "  • Delete remote branch: ${BLUE}git push origin --delete $MERGED_BRANCH${NC}"
    fi
    
    # Check for other copilot branches that might be stale
    echo -e "\n${YELLOW}📋 Other Copilot Branches:${NC}"
    git branch -r | grep "copilot/" | head -5 | while read branch; do
        echo -e "  • ${branch#  origin/}"
    done
}

# Main validation function
main() {
    local total_issues=0
    
    echo -e "\n${BLUE}🏁 Starting Post-Merge Validation${NC}"
    echo -e "${BLUE}==================================${NC}"
    
    # Run all validation checks
    validate_merge_integration
    total_issues=$((total_issues + $?))
    
    validate_branch_cleanup
    total_issues=$((total_issues + $?))
    
    validate_repository_structure
    total_issues=$((total_issues + $?))
    
    check_residual_issues
    total_issues=$((total_issues + $?))
    
    validate_working_tree
    total_issues=$((total_issues + $?))
    
    # Generate summary
    echo -e "\n${BLUE}📊 Validation Summary${NC}"
    echo -e "${BLUE}===================${NC}"
    
    if [ $total_issues -eq 0 ]; then
        print_status "PASS" "All validation checks passed successfully"
    else
        print_status "WARN" "Found $total_issues issue(s) that need attention"
    fi
    
    # Generate recommendations
    generate_cleanup_recommendations
    
    echo -e "\n${BLUE}📝 Next Steps:${NC}"
    echo -e "  1. Review any warnings or failures above"
    echo -e "  2. Execute recommended cleanup commands"
    echo -e "  3. Re-run this script to verify fixes"
    echo -e "  4. Update project documentation if needed"
    
    return $total_issues
}

# Execute main function
main "$@"