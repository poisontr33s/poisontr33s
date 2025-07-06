#!/bin/bash

# Example usage of GitHub Contributor Automation
# This script demonstrates how to use the automation system

echo "GitHub Contributor Automation - Usage Examples"
echo "=============================================="

# Check if required environment variables are set
if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPOSITORY" ]; then
    echo "Please set the following environment variables:"
    echo "  export GITHUB_TOKEN=\"your_github_token\""
    echo "  export GITHUB_REPOSITORY=\"owner/repo\""
    echo ""
    echo "Example:"
    echo "  export GITHUB_TOKEN=\"ghp_xxxxxxxxxxxxxxxxxxxx\""
    echo "  export GITHUB_REPOSITORY=\"myorg/myrepo\""
    exit 1
fi

echo "Environment variables set:"
echo "  GITHUB_REPOSITORY: $GITHUB_REPOSITORY"
echo "  GITHUB_TOKEN: ${GITHUB_TOKEN:0:10}..."
echo ""

# Example 1: Add contributor by username
echo "Example 1: Add contributor by username"
echo "Command: ./scripts/add_contributors.sh --username \"example-user\" --permission \"pull\""
echo "(This is a dry run - replace 'example-user' with actual username)"
echo ""

# Example 2: Add contributor by email
echo "Example 2: Add contributor by email"
echo "Command: ./scripts/add_contributors.sh --email \"user@example.com\" --permission \"push\""
echo "(This is a dry run - replace with actual email)"
echo ""

# Example 3: Process batch file
echo "Example 3: Process batch file"
echo "Command: ./scripts/add_contributors.sh --batch \"examples/batch-contributors.json\""
echo "Batch file contents:"
cat examples/batch-contributors.json
echo ""

# Example 4: Using Python script directly
echo "Example 4: Using Python script directly"
echo "Command: python3 scripts/add_contributors.py --username \"example-user\" --permission \"pull\""
echo ""

# Example 5: Test configuration loading
echo "Example 5: Test configuration loading"
echo "Testing configuration..."
python3 -c "
import sys
sys.path.append('scripts')
from add_contributors import ContributorAutomation
automation = ContributorAutomation()
print('✅ Configuration loaded successfully')
print(f'Default permission: {automation.config[\"default_permission\"]}')
print(f'Available permissions: {list(automation.config[\"permission_levels\"].values())}')
"

echo ""
echo "For more examples and documentation, see:"
echo "  - docs/contributor-automation.md"
echo "  - CONTRIBUTOR_AUTOMATION.md"
echo ""
echo "To run the full test suite:"
echo "  python3 tests/test_contributor_automation.py"