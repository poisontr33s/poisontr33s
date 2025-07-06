# GitHub Contributor Automation

This documentation provides comprehensive guidance on using the GitHub Contributor Automation system to dynamically add collaborators to your repository.

## Overview

The GitHub Contributor Automation system allows repository owners to:
- Add contributors by username or email address
- Specify permission levels for each contributor
- Process multiple contributors in batch operations
- Handle errors gracefully with comprehensive logging
- Use both command-line interface and GitHub Actions workflow

## Prerequisites

### Required Permissions
- **Repository admin access**: You must be an admin of the target repository
- **GitHub token**: Personal access token with the following scopes:
  - `repo` - Full repository access
  - `admin:org` - Organization admin access (if adding to organization repository)

### Required Software
- Python 3.7 or higher
- PyGithub library (`pip install PyGithub`)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/poisontr33s/poisontr33s.git
   cd poisontr33s
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   export GITHUB_REPOSITORY="owner/repository-name"
   ```

## Usage

### Command-Line Interface

#### Add Single Contributor by Username
```bash
python scripts/add_contributors.py \
  --username "contributor-username" \
  --permission "pull" \
  --repository "owner/repo" \
  --token "your_github_token"
```

#### Add Single Contributor by Email
```bash
python scripts/add_contributors.py \
  --email "contributor@example.com" \
  --permission "push" \
  --repository "owner/repo" \
  --token "your_github_token"
```

#### Process Batch File
```bash
python scripts/add_contributors.py \
  --batch-file "examples/batch-contributors.json" \
  --repository "owner/repo" \
  --token "your_github_token"
```

#### Using Environment Variables
```bash
# Set environment variables
export GITHUB_TOKEN="your_github_token"
export GITHUB_REPOSITORY="owner/repo"

# Run with simplified command
python scripts/add_contributors.py --username "contributor-username" --permission "pull"
```

### GitHub Actions Workflow

The system includes a GitHub Actions workflow that can be triggered manually from the GitHub web interface.

#### Manual Trigger
1. Go to your repository on GitHub
2. Navigate to **Actions** tab
3. Select **Add Contributors** workflow
4. Click **Run workflow**
5. Fill in the required parameters:
   - **Contributor Type**: Choose between `username` or `email`
   - **Contributor Identifier**: Enter the username or email
   - **Permission Level**: Select appropriate permission level
   - **Batch File** (optional): Path to batch file for multiple contributors

#### Workflow Features
- Automatic logging and artifact upload
- Success/failure notifications
- Support for both single and batch operations
- Comprehensive error handling

## Permission Levels

The system supports all GitHub collaboration permission levels:

| Permission | Description |
|------------|-------------|
| `pull` | Read-only access (default) |
| `push` | Read and write access |
| `triage` | Read access + issue and PR management |
| `maintain` | Push access + repository management (no admin) |
| `admin` | Full repository access including settings |

## Configuration

### Configuration File: `config/contributor-config.json`

```json
{
  "permission_levels": {
    "read": "pull",
    "write": "push",
    "admin": "admin",
    "maintain": "maintain",
    "triage": "triage"
  },
  "default_permission": "pull",
  "logging": {
    "level": "INFO",
    "file": "logs/contributor-automation.log",
    "console": true
  },
  "api": {
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 2
  },
  "validation": {
    "validate_username": true,
    "validate_email": true,
    "check_user_exists": true
  }
}
```

### Batch File Format

For batch operations, create a JSON file with the following structure:

```json
[
  {
    "username": "contributor1",
    "permission": "pull"
  },
  {
    "username": "contributor2",
    "permission": "push"
  },
  {
    "email": "contributor@example.com",
    "permission": "pull"
  }
]
```

## Error Handling

The system provides comprehensive error handling for common scenarios:

### Common Errors and Solutions

#### 1. **User Not Found**
- **Error**: `User not found: username`
- **Solution**: Verify the username is correct and the user exists on GitHub

#### 2. **Insufficient Permissions**
- **Error**: `Insufficient permissions to add collaborator`
- **Solution**: Ensure your GitHub token has `repo` and `admin:org` scopes

#### 3. **Invalid Permission Level**
- **Error**: `Invalid permission level: invalid_permission`
- **Solution**: Use one of: `pull`, `push`, `triage`, `maintain`, `admin`

#### 4. **User Already Collaborator**
- **Warning**: `User username is already a collaborator`
- **Action**: No action needed, operation continues

#### 5. **API Rate Limiting**
- **Error**: `API rate limit exceeded`
- **Solution**: Wait for rate limit reset or use authenticated requests

#### 6. **Network/Connection Issues**
- **Error**: `Connection timeout` or `Network error`
- **Solution**: Check internet connection, retry operation

## Logging

The system provides detailed logging at multiple levels:

### Log Levels
- **INFO**: General operations and success messages
- **WARNING**: Non-critical issues that don't prevent operation
- **ERROR**: Critical issues that prevent operation

### Log Locations
- **File**: `logs/contributor-automation.log`
- **Console**: Real-time output during execution
- **GitHub Actions**: Workflow logs and artifacts

### Example Log Output
```
2024-01-15 10:30:15 - contributor-automation - INFO - Successfully connected to repository: owner/repo
2024-01-15 10:30:16 - contributor-automation - INFO - Successfully added contributor1 as collaborator with pull permission
2024-01-15 10:30:17 - contributor-automation - WARNING - User contributor2 is already a collaborator
2024-01-15 10:30:18 - contributor-automation - ERROR - User not found: invalid-user
```

## Security Considerations

### Token Security
- Never commit GitHub tokens to version control
- Use environment variables or GitHub Secrets for tokens
- Regularly rotate access tokens
- Use minimum required permissions

### Repository Access
- Only grant necessary permission levels
- Regularly audit repository collaborators
- Monitor automation logs for unauthorized access attempts

### Validation
- The system validates usernames and emails before processing
- Checks for existing collaborators to prevent duplicates
- Implements retry logic for transient network issues

## Troubleshooting

### Common Issues

#### Script Not Found
```bash
# Make sure you're in the right directory
cd /path/to/poisontr33s
python scripts/add_contributors.py --help
```

#### Permission Denied
```bash
# Make the script executable
chmod +x scripts/add_contributors.py
```

#### PyGithub Import Error
```bash
# Install the required library
pip install PyGithub
```

#### Configuration File Not Found
```bash
# Check if config file exists
ls -la config/contributor-config.json
```

### Debug Mode
Enable debug logging by modifying the configuration:
```json
{
  "logging": {
    "level": "DEBUG",
    "file": "logs/contributor-automation.log",
    "console": true
  }
}
```

## API Rate Limits

GitHub API has rate limits that may affect batch operations:

- **Authenticated requests**: 5,000 requests per hour
- **Search API**: 30 requests per minute
- **Adding collaborators**: No specific limit, subject to general rate limits

### Rate Limit Handling
The system implements automatic retry logic with exponential backoff to handle rate limiting gracefully.

## Examples

### Example 1: Add Single Contributor
```bash
python scripts/add_contributors.py \
  --username "johndoe" \
  --permission "push" \
  --repository "myorg/myrepo" \
  --token "ghp_xxxxxxxxxxxxxxxxxxxx"
```

### Example 2: Add Multiple Contributors
Create `my-contributors.json`:
```json
[
  {"username": "developer1", "permission": "push"},
  {"username": "designer1", "permission": "pull"},
  {"email": "contractor@example.com", "permission": "pull"}
]
```

Run batch operation:
```bash
python scripts/add_contributors.py \
  --batch-file "my-contributors.json" \
  --repository "myorg/myrepo" \
  --token "ghp_xxxxxxxxxxxxxxxxxxxx"
```

### Example 3: Using Environment Variables
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITHUB_REPOSITORY="myorg/myrepo"

python scripts/add_contributors.py --username "newdev" --permission "pull"
```

## Limitations

1. **Email Search**: GitHub's email search is limited and may not find all users
2. **Private Repositories**: Requires appropriate access tokens
3. **Organization Repositories**: May require additional organization permissions
4. **Rate Limits**: Large batch operations may be throttled by GitHub API limits
5. **User Acceptance**: Added collaborators must accept the invitation to gain access

## Support

For issues, questions, or contributions:
1. Check the logs for detailed error information
2. Verify your GitHub token has the correct permissions
3. Ensure you have admin access to the target repository
4. Review the troubleshooting section above

## License

This automation system is part of the poisontr33s repository and follows the same licensing terms.