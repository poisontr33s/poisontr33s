# GitHub Contributor Automation

## Quick Start

The repository includes an automated system for adding contributors to GitHub repositories.

### Command Line Usage

```bash
# Add a contributor by username
./scripts/add_contributors.sh --username "newcontributor" --permission "pull"

# Add a contributor by email
./scripts/add_contributors.sh --email "user@example.com" --permission "push"

# Process multiple contributors from a file
./scripts/add_contributors.sh --batch "examples/batch-contributors.json"
```

### GitHub Actions Workflow

1. Go to the **Actions** tab in your repository
2. Select **Add Contributors** workflow
3. Click **Run workflow**
4. Fill in the contributor details
5. Click **Run workflow** to execute

### Prerequisites

- Repository admin permissions
- GitHub token with `repo` and `admin:org` scopes
- Python 3.7+ with PyGithub library

### Permission Levels

- `pull` - Read-only access (default)
- `push` - Read and write access
- `triage` - Read access + issue management
- `maintain` - Push access + repository management
- `admin` - Full repository access

For complete documentation, see [docs/contributor-automation.md](docs/contributor-automation.md).

## Features

- ✅ Add contributors by username or email
- ✅ Configurable permission levels
- ✅ Batch processing support
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ GitHub Actions integration
- ✅ Command-line interface
- ✅ Shell script wrapper for ease of use