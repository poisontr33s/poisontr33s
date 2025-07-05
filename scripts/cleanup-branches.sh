#!/bin/bash

# Branch Cleanup Script for Post-Merge Operations
# Safely removes merged branches locally and remotely

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default branch to clean up
DEFAULT_BRANCH="copilot/fix-71a13388-9183-473b-a4d1-dadd0595d643"

echo -e "${BLUE}🧹 Branch Cleanup Tool${NC}"
echo -e "${BLUE}======================${NC}"

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ SUCCESS:${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}❌ ERROR:${NC} $message"
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
    if git ls-remote --heads origin "$branch_name" 2>/dev/null | grep -q "$branch_name"; then
        return 0
    else
        return 1
    fi
}

# Function to safely delete local branch
delete_local_branch() {
    local branch_name=$1
    
    print_status "INFO" "Checking local branch: $branch_name"
    
    if check_local_branch "$branch_name"; then
        # Check if we're currently on this branch
        current_branch=$(git rev-parse --abbrev-ref HEAD)
        if [ "$current_branch" = "$branch_name" ]; then
            print_status "WARN" "Currently on branch $branch_name, switching to main"
            git checkout main || git checkout master || {
                print_status "ERROR" "Could not switch to main/master branch"
                return 1
            }
        fi
        
        # Try to delete the branch
        if git branch -d "$branch_name" 2>/dev/null; then
            print_status "SUCCESS" "Local branch $branch_name deleted successfully"
        elif git branch -D "$branch_name" 2>/dev/null; then
            print_status "SUCCESS" "Local branch $branch_name force-deleted successfully"
        else
            print_status "ERROR" "Failed to delete local branch $branch_name"
            return 1
        fi
    else
        print_status "INFO" "Local branch $branch_name does not exist (already cleaned up)"
    fi
    
    return 0
}

# Function to safely delete remote branch
delete_remote_branch() {
    local branch_name=$1
    
    print_status "INFO" "Checking remote branch: $branch_name"
    
    if check_remote_branch "$branch_name"; then
        # Confirm deletion
        echo -e "${YELLOW}Are you sure you want to delete remote branch '$branch_name'? (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            if git push origin --delete "$branch_name" 2>/dev/null; then
                print_status "SUCCESS" "Remote branch $branch_name deleted successfully"
            else
                print_status "ERROR" "Failed to delete remote branch $branch_name"
                print_status "INFO" "You may need elevated permissions or the branch may be protected"
                return 1
            fi
        else
            print_status "INFO" "Remote branch deletion cancelled by user"
        fi
    else
        print_status "INFO" "Remote branch $branch_name does not exist (already cleaned up)"
    fi
    
    return 0
}

# Function to list copilot branches
list_copilot_branches() {
    print_status "INFO" "Listing all copilot branches..."
    
    echo -e "\n${BLUE}📋 Local Copilot Branches:${NC}"
    local local_branches=$(git branch --list "copilot/*" | sed 's/^[ *]*//' | head -10)
    if [ -z "$local_branches" ]; then
        echo "  (none found)"
    else
        echo "$local_branches" | while read branch; do
            echo "  • $branch"
        done
    fi
    
    echo -e "\n${BLUE}📋 Remote Copilot Branches:${NC}"
    local remote_branches=$(git ls-remote --heads origin 2>/dev/null | grep "copilot/" | cut -d'/' -f3- | head -10)
    if [ -z "$remote_branches" ]; then
        echo "  (none found)"
    else
        echo "$remote_branches" | while read branch; do
            echo "  • $branch"
        done
    fi
}

# Function to interactive cleanup
interactive_cleanup() {
    echo -e "\n${BLUE}🔧 Interactive Branch Cleanup${NC}"
    echo -e "${BLUE}==============================${NC}"
    
    # List all copilot branches
    list_copilot_branches
    
    echo -e "\n${YELLOW}Enter branch name to clean up (or press Enter for default):${NC}"
    read -r branch_input
    
    if [ -z "$branch_input" ]; then
        branch_to_clean="$DEFAULT_BRANCH"
    else
        branch_to_clean="$branch_input"
    fi
    
    echo -e "\n${BLUE}Cleaning up branch: $branch_to_clean${NC}"
    
    # Clean up local branch
    delete_local_branch "$branch_to_clean"
    
    # Clean up remote branch
    delete_remote_branch "$branch_to_clean"
    
    # Clean up remote tracking references
    print_status "INFO" "Cleaning up remote tracking references..."
    git remote prune origin 2>/dev/null || print_status "WARN" "Could not prune remote references"
    
    echo -e "\n${GREEN}🎉 Cleanup completed for: $branch_to_clean${NC}"
}

# Function to batch cleanup
batch_cleanup() {
    local branches_to_clean=("$@")
    
    if [ ${#branches_to_clean[@]} -eq 0 ]; then
        branches_to_clean=("$DEFAULT_BRANCH")
    fi
    
    echo -e "\n${BLUE}🔧 Batch Branch Cleanup${NC}"
    echo -e "${BLUE}========================${NC}"
    
    for branch in "${branches_to_clean[@]}"; do
        echo -e "\n${YELLOW}Processing branch: $branch${NC}"
        delete_local_branch "$branch"
        delete_remote_branch "$branch"
    done
    
    # Clean up remote tracking references
    print_status "INFO" "Cleaning up remote tracking references..."
    git remote prune origin 2>/dev/null || print_status "WARN" "Could not prune remote references"
    
    echo -e "\n${GREEN}🎉 Batch cleanup completed${NC}"
}

# Function to show help
show_help() {
    cat << EOF
Branch Cleanup Tool - Post-Merge Operations

Usage: $0 [OPTIONS] [BRANCH_NAMES...]

Options:
  -i, --interactive    Interactive cleanup mode
  -l, --list          List copilot branches only
  -h, --help          Show this help message

Examples:
  $0                                    # Clean up default branch
  $0 copilot/fix-abc123                 # Clean up specific branch
  $0 copilot/fix-abc123 copilot/fix-def456  # Clean up multiple branches
  $0 -i                                 # Interactive mode
  $0 -l                                 # List branches only

Default branch: $DEFAULT_BRANCH
EOF
}

# Main function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interactive)
                interactive_cleanup
                exit 0
                ;;
            -l|--list)
                list_copilot_branches
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                # Remaining arguments are branch names
                break
                ;;
        esac
        shift
    done
    
    # If no specific mode, run batch cleanup
    if [ $# -eq 0 ]; then
        batch_cleanup
    else
        batch_cleanup "$@"
    fi
}

# Safety check - ensure we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_status "ERROR" "Not in a git repository"
    exit 1
fi

# Run main function with all arguments
main "$@"