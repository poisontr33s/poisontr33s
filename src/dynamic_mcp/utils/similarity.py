"""
Similarity calculation utilities
"""

import logging
from typing import List, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


class SimilarityCalculator:
    """Calculate text similarity using various methods"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using TF-IDF and cosine similarity.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        try:
            # Vectorize texts
            vectors = self.tfidf_vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(vectors)
            
            # Return similarity between the two texts
            return float(similarity_matrix[0, 1])
            
        except Exception as e:
            self.logger.error(f"Error calculating text similarity: {str(e)}")
            return 0.0
    
    def calculate_batch_similarity(self, query_text: str, texts: List[str]) -> List[Tuple[int, float]]:
        """
        Calculate similarity between a query and multiple texts.
        
        Args:
            query_text: Query text
            texts: List of texts to compare against
            
        Returns:
            List of (index, similarity_score) tuples sorted by similarity
        """
        if not query_text or not texts:
            return []
        
        try:
            # Combine query with all texts
            all_texts = [query_text] + texts
            
            # Vectorize all texts
            vectors = self.tfidf_vectorizer.fit_transform(all_texts)
            
            # Calculate similarities with query (first vector)
            query_vector = vectors[0:1]
            text_vectors = vectors[1:]
            
            similarities = cosine_similarity(query_vector, text_vectors)[0]
            
            # Create list of (index, similarity) tuples
            similarity_pairs = [(i, float(sim)) for i, sim in enumerate(similarities)]
            
            # Sort by similarity (descending)
            similarity_pairs.sort(key=lambda x: x[1], reverse=True)
            
            return similarity_pairs
            
        except Exception as e:
            self.logger.error(f"Error calculating batch similarity: {str(e)}")
            return []


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Convenience function to calculate similarity between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    calculator = SimilarityCalculator()
    return calculator.calculate_text_similarity(text1, text2)