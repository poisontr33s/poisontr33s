#!/usr/bin/env python3
"""
GitHub Contributor Automation Script

This script automates the process of adding contributors to a GitHub repository
using the GitHub API. It supports adding users by username or email with
configurable permission levels.

Usage:
    python add_contributors.py --username <username> --permission <level>
    python add_contributors.py --email <email> --permission <level>
    python add_contributors.py --config-file <path> --batch-file <path>

Requirements:
    - PyGithub library
    - GitHub token with appropriate permissions (repo, admin:org)
    - Repository admin access
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

try:
    from github import Github, GithubException
    from github.Repository import Repository
except ImportError:
    print("Error: PyGithub library not found. Install with: pip install PyGithub")
    sys.exit(1)


class ContributorAutomation:
    """Main class for handling contributor automation."""
    
    def __init__(self, config_path: str = "config/contributor-config.json"):
        """Initialize the automation system."""
        self.config = self._load_config(config_path)
        self.github = None
        self.repo = None
        self.logger = self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Configuration file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in configuration file: {e}")
            sys.exit(1)
            
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('contributor-automation')
        logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        # Create logs directory if it doesn't exist
        log_file = self.config['logging']['file']
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        if self.config['logging']['console']:
            logger.addHandler(console_handler)
            
        return logger
        
    def initialize_github(self, token: str, repository: str) -> bool:
        """Initialize GitHub API connection."""
        try:
            self.github = Github(token, timeout=self.config['api']['timeout'])
            self.repo = self.github.get_repo(repository)
            self.logger.info(f"Successfully connected to repository: {repository}")
            return True
        except GithubException as e:
            self.logger.error(f"Failed to connect to GitHub: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during GitHub initialization: {e}")
            return False
            
    def validate_permission(self, permission: str) -> bool:
        """Validate permission level."""
        valid_permissions = list(self.config['permission_levels'].values())
        if permission not in valid_permissions:
            self.logger.error(
                f"Invalid permission level: {permission}. "
                f"Valid options: {', '.join(valid_permissions)}"
            )
            return False
        return True
        
    def get_user_by_username(self, username: str) -> Optional[object]:
        """Get GitHub user by username."""
        try:
            user = self.github.get_user(username)
            # Trigger API call to check if user exists
            _ = user.login
            return user
        except GithubException as e:
            if e.status == 404:
                self.logger.error(f"User not found: {username}")
            else:
                self.logger.error(f"Error getting user {username}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting user {username}: {e}")
            return None
            
    def get_user_by_email(self, email: str) -> Optional[object]:
        """Get GitHub user by email (search)."""
        try:
            # Search for users by email
            users = self.github.search_users(f"{email} in:email")
            user_list = list(users)
            
            if not user_list:
                self.logger.error(f"No user found with email: {email}")
                return None
                
            if len(user_list) > 1:
                self.logger.warning(
                    f"Multiple users found with email {email}. "
                    f"Using first result: {user_list[0].login}"
                )
                
            return user_list[0]
        except GithubException as e:
            self.logger.error(f"Error searching for user with email {email}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error searching for user with email {email}: {e}")
            return None
            
    def add_contributor(self, username: str = None, email: str = None, 
                       permission: str = None) -> bool:
        """Add a contributor to the repository."""
        if not self.github or not self.repo:
            self.logger.error("GitHub connection not initialized")
            return False
            
        # Use default permission if not specified
        if not permission:
            permission = self.config['default_permission']
            
        # Validate permission
        if not self.validate_permission(permission):
            return False
            
        # Get user object
        user = None
        if username:
            user = self.get_user_by_username(username)
            identifier = username
        elif email:
            user = self.get_user_by_email(email)
            identifier = email
        else:
            self.logger.error("Either username or email must be provided")
            return False
            
        if not user:
            return False
            
        # Check if user is already a collaborator
        try:
            if self.repo.has_in_collaborators(user):
                self.logger.warning(
                    f"User {user.login} is already a collaborator"
                )
                return True
        except GithubException as e:
            self.logger.error(f"Error checking collaborator status: {e}")
            return False
            
        # Add user as collaborator with retry logic
        for attempt in range(self.config['api']['retry_attempts']):
            try:
                self.repo.add_to_collaborators(user, permission)
                self.logger.info(
                    f"Successfully added {user.login} as collaborator "
                    f"with {permission} permission"
                )
                return True
            except GithubException as e:
                if e.status == 403:
                    self.logger.error(
                        f"Insufficient permissions to add collaborator: {e}"
                    )
                    return False
                elif e.status == 422:
                    self.logger.error(
                        f"Invalid request when adding collaborator: {e}"
                    )
                    return False
                else:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {e}"
                    )
                    if attempt < self.config['api']['retry_attempts'] - 1:
                        time.sleep(self.config['api']['retry_delay'])
                    else:
                        self.logger.error(
                            f"Failed to add collaborator after "
                            f"{self.config['api']['retry_attempts']} attempts"
                        )
                        return False
            except Exception as e:
                self.logger.error(f"Unexpected error adding collaborator: {e}")
                return False
                
        return False
        
    def process_batch_file(self, batch_file: str) -> Tuple[int, int]:
        """Process a batch file with multiple contributors."""
        try:
            with open(batch_file, 'r') as f:
                contributors = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Batch file not found: {batch_file}")
            return 0, 0
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in batch file: {e}")
            return 0, 0
            
        success_count = 0
        total_count = len(contributors)
        
        for contributor in contributors:
            username = contributor.get('username')
            email = contributor.get('email')
            permission = contributor.get('permission', self.config['default_permission'])
            
            if self.add_contributor(username=username, email=email, permission=permission):
                success_count += 1
                
        self.logger.info(f"Batch processing complete: {success_count}/{total_count} successful")
        return success_count, total_count


def main():
    """Main function to handle command-line arguments and execution."""
    parser = argparse.ArgumentParser(
        description="Automate adding contributors to GitHub repositories"
    )
    parser.add_argument(
        '--username', '-u', 
        help="GitHub username of the contributor to add"
    )
    parser.add_argument(
        '--email', '-e', 
        help="Email address of the contributor to add"
    )
    parser.add_argument(
        '--permission', '-p', 
        help="Permission level (pull, push, admin, maintain, triage)"
    )
    parser.add_argument(
        '--repository', '-r', 
        help="Repository in format owner/repo (can also use GITHUB_REPOSITORY env var)"
    )
    parser.add_argument(
        '--token', '-t', 
        help="GitHub token (can also use GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        '--config-file', '-c', 
        default="config/contributor-config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        '--batch-file', '-b', 
        help="Path to JSON file with multiple contributors"
    )
    
    args = parser.parse_args()
    
    # Get token and repository from environment if not provided
    token = args.token or os.getenv('GITHUB_TOKEN')
    repository = args.repository or os.getenv('GITHUB_REPOSITORY')
    
    if not token:
        print("Error: GitHub token required. Use --token or set GITHUB_TOKEN environment variable.")
        sys.exit(1)
        
    if not repository:
        print("Error: Repository required. Use --repository or set GITHUB_REPOSITORY environment variable.")
        sys.exit(1)
        
    # Initialize automation system
    automation = ContributorAutomation(args.config_file)
    
    if not automation.initialize_github(token, repository):
        sys.exit(1)
        
    # Process batch file if provided
    if args.batch_file:
        success_count, total_count = automation.process_batch_file(args.batch_file)
        if success_count == total_count:
            print(f"All {total_count} contributors added successfully!")
        else:
            print(f"Added {success_count} out of {total_count} contributors")
            sys.exit(1)
    else:
        # Process single contributor
        if not args.username and not args.email:
            print("Error: Either --username or --email must be provided")
            sys.exit(1)
            
        if automation.add_contributor(
            username=args.username, 
            email=args.email, 
            permission=args.permission
        ):
            print("Contributor added successfully!")
        else:
            print("Failed to add contributor")
            sys.exit(1)


if __name__ == "__main__":
    main()