#!/usr/bin/env python3
"""
Test script for GitHub Contributor Automation

This script performs comprehensive tests of the contributor automation system
without making actual API calls to GitHub.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the scripts directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from add_contributors import ContributorAutomation
except ImportError as e:
    print(f"Error importing ContributorAutomation: {e}")
    sys.exit(1)


class TestContributorAutomation(unittest.TestCase):
    """Test cases for the ContributorAutomation class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.config_data = {
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
                "file": "test_logs/test.log",
                "console": False
            },
            "api": {
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 1
            },
            "validation": {
                "validate_username": True,
                "validate_email": True,
                "check_user_exists": True
            }
        }
        
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.config_data, self.temp_config)
        self.temp_config.close()
        
        # Create logs directory
        os.makedirs("test_logs", exist_ok=True)
        
        # Initialize automation with test config
        self.automation = ContributorAutomation(self.temp_config.name)
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary config file
        os.unlink(self.temp_config.name)
        
        # Clean up log files
        if os.path.exists("test_logs/test.log"):
            os.unlink("test_logs/test.log")
        if os.path.exists("test_logs"):
            os.rmdir("test_logs")
    
    def test_config_loading(self):
        """Test configuration loading."""
        self.assertEqual(self.automation.config['default_permission'], 'pull')
        self.assertEqual(self.automation.config['api']['timeout'], 30)
        self.assertEqual(self.automation.config['logging']['level'], 'INFO')
        
    def test_permission_validation(self):
        """Test permission validation."""
        # Valid permissions
        self.assertTrue(self.automation.validate_permission('pull'))
        self.assertTrue(self.automation.validate_permission('push'))
        self.assertTrue(self.automation.validate_permission('admin'))
        self.assertTrue(self.automation.validate_permission('maintain'))
        self.assertTrue(self.automation.validate_permission('triage'))
        
        # Invalid permissions
        self.assertFalse(self.automation.validate_permission('invalid'))
        self.assertFalse(self.automation.validate_permission(''))
        self.assertFalse(self.automation.validate_permission('write'))  # Should be 'push'
        
    @patch('add_contributors.Github')
    def test_github_initialization(self, mock_github):
        """Test GitHub API initialization."""
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_instance.get_repo.return_value = mock_repo
        
        result = self.automation.initialize_github('test_token', 'owner/repo')
        
        self.assertTrue(result)
        self.assertEqual(self.automation.github, mock_github_instance)
        self.assertEqual(self.automation.repo, mock_repo)
        mock_github.assert_called_once_with('test_token', timeout=30)
        mock_github_instance.get_repo.assert_called_once_with('owner/repo')
        
    @patch('add_contributors.Github')
    def test_github_initialization_failure(self, mock_github):
        """Test GitHub API initialization failure."""
        mock_github.side_effect = Exception("Connection failed")
        
        result = self.automation.initialize_github('test_token', 'owner/repo')
        
        self.assertFalse(result)
        self.assertIsNone(self.automation.github)
        self.assertIsNone(self.automation.repo)
        
    @patch('add_contributors.Github')
    def test_get_user_by_username(self, mock_github):
        """Test getting user by username."""
        mock_github_instance = Mock()
        mock_user = Mock()
        mock_user.login = 'testuser'
        
        self.automation.github = mock_github_instance
        mock_github_instance.get_user.return_value = mock_user
        
        result = self.automation.get_user_by_username('testuser')
        
        self.assertEqual(result, mock_user)
        mock_github_instance.get_user.assert_called_once_with('testuser')
        
    @patch('add_contributors.Github')
    def test_get_user_by_username_not_found(self, mock_github):
        """Test getting user by username when user not found."""
        mock_github_instance = Mock()
        mock_github_instance.get_user.side_effect = Exception("User not found")
        
        self.automation.github = mock_github_instance
        
        result = self.automation.get_user_by_username('nonexistent')
        
        self.assertIsNone(result)
        
    @patch('add_contributors.Github')
    def test_get_user_by_email(self, mock_github):
        """Test getting user by email."""
        mock_github_instance = Mock()
        mock_user = Mock()
        mock_user.login = 'testuser'
        
        self.automation.github = mock_github_instance
        mock_github_instance.search_users.return_value = [mock_user]
        
        result = self.automation.get_user_by_email('test@example.com')
        
        self.assertEqual(result, mock_user)
        mock_github_instance.search_users.assert_called_once_with('test@example.com in:email')
        
    def test_batch_file_processing(self):
        """Test batch file processing."""
        # Create a temporary batch file
        batch_data = [
            {"username": "user1", "permission": "pull"},
            {"username": "user2", "permission": "push"},
            {"email": "user3@example.com", "permission": "admin"}
        ]
        
        temp_batch = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(batch_data, temp_batch)
        temp_batch.close()
        
        try:
            # Mock the add_contributor method to always return True
            with patch.object(self.automation, 'add_contributor', return_value=True):
                success_count, total_count = self.automation.process_batch_file(temp_batch.name)
                
                self.assertEqual(success_count, 3)
                self.assertEqual(total_count, 3)
        finally:
            # Clean up
            os.unlink(temp_batch.name)
            
    def test_batch_file_not_found(self):
        """Test batch file processing when file doesn't exist."""
        success_count, total_count = self.automation.process_batch_file('nonexistent.json')
        
        self.assertEqual(success_count, 0)
        self.assertEqual(total_count, 0)


class TestConfiguration(unittest.TestCase):
    """Test configuration handling."""
    
    def test_invalid_config_file(self):
        """Test behavior with invalid config file."""
        with self.assertRaises(SystemExit):
            ContributorAutomation('nonexistent_config.json')
            
    def test_invalid_json_config(self):
        """Test behavior with invalid JSON in config file."""
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_config.write('invalid json content')
        temp_config.close()
        
        try:
            with self.assertRaises(SystemExit):
                ContributorAutomation(temp_config.name)
        finally:
            os.unlink(temp_config.name)


def run_functional_tests():
    """Run functional tests without GitHub API calls."""
    print("Running functional tests...")
    
    # Test 1: Configuration loading
    print("Test 1: Configuration loading")
    try:
        automation = ContributorAutomation()
        print("✅ Configuration loaded successfully")
        print(f"   Default permission: {automation.config['default_permission']}")
        print(f"   Available permissions: {list(automation.config['permission_levels'].values())}")
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False
    
    # Test 2: Permission validation
    print("\nTest 2: Permission validation")
    valid_perms = ['pull', 'push', 'admin', 'maintain', 'triage']
    invalid_perms = ['invalid', 'write', '', 'read']
    
    all_passed = True
    for perm in valid_perms:
        if not automation.validate_permission(perm):
            print(f"❌ Valid permission '{perm}' failed validation")
            all_passed = False
    
    for perm in invalid_perms:
        if automation.validate_permission(perm):
            print(f"❌ Invalid permission '{perm}' passed validation")
            all_passed = False
    
    if all_passed:
        print("✅ Permission validation working correctly")
    
    # Test 3: Batch file format validation
    print("\nTest 3: Batch file format validation")
    try:
        with open('examples/batch-contributors.json', 'r') as f:
            batch_data = json.load(f)
        
        required_fields = ['username', 'permission']
        valid_batch = True
        
        for contributor in batch_data:
            if not any(field in contributor for field in ['username', 'email']):
                print(f"❌ Contributor missing username/email: {contributor}")
                valid_batch = False
            if 'permission' not in contributor:
                print(f"❌ Contributor missing permission: {contributor}")
                valid_batch = False
        
        if valid_batch:
            print("✅ Batch file format validation passed")
        
    except Exception as e:
        print(f"❌ Batch file validation failed: {e}")
        all_passed = False
    
    # Test 4: Directory structure
    print("\nTest 4: Directory structure")
    required_dirs = ['scripts', 'config', 'docs', 'examples', '.github/workflows']
    required_files = [
        'scripts/add_contributors.py',
        'scripts/add_contributors.sh',
        'config/contributor-config.json',
        'docs/contributor-automation.md',
        'examples/batch-contributors.json',
        '.github/workflows/add-contributors.yml'
    ]
    
    structure_valid = True
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ Missing directory: {directory}")
            structure_valid = False
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing file: {file_path}")
            structure_valid = False
    
    if structure_valid:
        print("✅ Directory structure validation passed")
    
    return all_passed


def main():
    """Main test runner."""
    print("GitHub Contributor Automation - Test Suite")
    print("=" * 50)
    
    # Run unit tests
    print("\nRunning unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run functional tests
    print("\n" + "=" * 50)
    success = run_functional_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())