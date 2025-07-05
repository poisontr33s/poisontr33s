"""
Text processing utilities for RAG and content analysis
"""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import string


class TextProcessor:
    """
    Utilities for processing and analyzing text content.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common stop words for filtering
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 
            'its', 'our', 'their'
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        try:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Remove URLs
            text = re.sub(r'https?://[^\s]+', '', text)
            
            # Remove email addresses
            text = re.sub(r'\S+@\S+', '', text)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove leading/trailing whitespace
            text = text.strip()
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {str(e)}")
            return text
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords
        """
        if not text:
            return []
        
        try:
            # Clean and normalize text
            cleaned_text = self.clean_text(text.lower())
            
            # Split into words
            words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_text)
            
            # Filter out stop words
            filtered_words = [word for word in words if word not in self.stop_words]
            
            # Count word frequencies
            word_counts = {}
            for word in filtered_words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # Sort by frequency and return top keywords
            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, count in sorted_words[:max_keywords]]
            
            return keywords
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        try:
            chunks = []
            start = 0
            
            while start < len(text):
                # Find the end of this chunk
                end = start + chunk_size
                
                # If we're not at the end of the text, try to break at a word boundary
                if end < len(text):
                    # Look for the last space before the end position
                    last_space = text.rfind(' ', start, end)
                    if last_space > start:
                        end = last_space
                
                # Extract the chunk
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                
                # Move to the next chunk with overlap
                start = end - overlap
                if start < 0:
                    start = 0
                
                # If we didn't advance, break to avoid infinite loop
                if start >= end:
                    break
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error chunking text: {str(e)}")
            return [text]
    
    def extract_code_snippets(self, text: str) -> List[Dict[str, str]]:
        """
        Extract code snippets from text.
        
        Args:
            text: Text containing code snippets
            
        Returns:
            List of code snippets with metadata
        """
        if not text:
            return []
        
        try:
            snippets = []
            
            # Find code blocks (markdown style)
            code_block_pattern = r'```(\w+)?\s*\n(.*?)\n```'
            matches = re.findall(code_block_pattern, text, re.DOTALL)
            
            for language, code in matches:
                snippets.append({
                    'language': language or 'unknown',
                    'code': code.strip(),
                    'type': 'code_block'
                })
            
            # Find inline code
            inline_code_pattern = r'`([^`]+)`'
            inline_matches = re.findall(inline_code_pattern, text)
            
            for code in inline_matches:
                if len(code) > 5:  # Only include substantial inline code
                    snippets.append({
                        'language': 'unknown',
                        'code': code.strip(),
                        'type': 'inline_code'
                    })
            
            return snippets
            
        except Exception as e:
            self.logger.error(f"Error extracting code snippets: {str(e)}")
            return []
    
    def analyze_content_type(self, text: str) -> Dict[str, Any]:
        """
        Analyze the type and characteristics of content.
        
        Args:
            text: Text to analyze
            
        Returns:
            Analysis results
        """
        if not text:
            return {'type': 'empty', 'confidence': 1.0}
        
        try:
            analysis = {
                'length': len(text),
                'word_count': len(text.split()),
                'line_count': len(text.split('\n')),
                'has_code': False,
                'has_urls': False,
                'has_numbers': False,
                'language_indicators': [],
                'content_type': 'unknown',
                'confidence': 0.0,
            }
            
            # Check for code
            code_indicators = ['def ', 'function ', 'class ', 'import ', 'from ', '{', '}', '()', '=>']
            if any(indicator in text for indicator in code_indicators):
                analysis['has_code'] = True
                analysis['language_indicators'].extend([ind for ind in code_indicators if ind in text])
            
            # Check for URLs
            if re.search(r'https?://[^\s]+', text):
                analysis['has_urls'] = True
            
            # Check for numbers
            if re.search(r'\d+', text):
                analysis['has_numbers'] = True
            
            # Determine content type
            if analysis['has_code']:
                analysis['content_type'] = 'code'
                analysis['confidence'] = 0.8
            elif 'error' in text.lower() or 'exception' in text.lower():
                analysis['content_type'] = 'error'
                analysis['confidence'] = 0.9
            elif any(word in text.lower() for word in ['todo', 'fixme', 'bug', 'issue']):
                analysis['content_type'] = 'issue'
                analysis['confidence'] = 0.7
            elif any(word in text.lower() for word in ['deploy', 'release', 'build']):
                analysis['content_type'] = 'deployment'
                analysis['confidence'] = 0.6
            elif any(word in text.lower() for word in ['test', 'spec', 'assert']):
                analysis['content_type'] = 'testing'
                analysis['confidence'] = 0.7
            elif any(word in text.lower() for word in ['doc', 'readme', 'guide', 'manual']):
                analysis['content_type'] = 'documentation'
                analysis['confidence'] = 0.8
            else:
                analysis['content_type'] = 'general'
                analysis['confidence'] = 0.5
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing content type: {str(e)}")
            return {'type': 'error', 'confidence': 0.0, 'error': str(e)}
    
    def extract_github_references(self, text: str) -> Dict[str, List[str]]:
        """
        Extract GitHub-specific references from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of GitHub references
        """
        if not text:
            return {}
        
        try:
            references = {
                'issues': [],
                'pull_requests': [],
                'commits': [],
                'repositories': [],
                'users': [],
            }
            
            # Find issue references (#123)
            issue_pattern = r'#(\d+)'
            references['issues'] = re.findall(issue_pattern, text)
            
            # Find PR references (PR #123, pull request #123)
            pr_pattern = r'(?:PR|pull request)\s*#(\d+)'
            references['pull_requests'] = re.findall(pr_pattern, text, re.IGNORECASE)
            
            # Find commit references (commit hash patterns)
            commit_pattern = r'\b[a-f0-9]{7,40}\b'
            potential_commits = re.findall(commit_pattern, text)
            # Filter out common false positives
            references['commits'] = [c for c in potential_commits if len(c) >= 7]
            
            # Find repository references (owner/repo)
            repo_pattern = r'\b([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)\b'
            references['repositories'] = re.findall(repo_pattern, text)
            
            # Find user mentions (@username)
            user_pattern = r'@([a-zA-Z0-9_-]+)'
            references['users'] = re.findall(user_pattern, text)
            
            return references
            
        except Exception as e:
            self.logger.error(f"Error extracting GitHub references: {str(e)}")
            return {}
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Create a summary of the text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Text summary
        """
        if not text:
            return ""
        
        try:
            # Clean text
            cleaned_text = self.clean_text(text)
            
            # If text is already short, return as-is
            if len(cleaned_text) <= max_length:
                return cleaned_text
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', cleaned_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # If we have sentences, take the first few that fit
            if sentences:
                summary = ""
                for sentence in sentences:
                    if len(summary + sentence) <= max_length - 3:  # Leave room for "..."
                        summary += sentence + ". "
                    else:
                        break
                
                if len(summary) < len(cleaned_text):
                    summary = summary.strip() + "..."
                
                return summary
            
            # Fallback: just truncate
            return cleaned_text[:max_length-3] + "..."
            
        except Exception as e:
            self.logger.error(f"Error summarizing text: {str(e)}")
            return text[:max_length] if len(text) > max_length else text