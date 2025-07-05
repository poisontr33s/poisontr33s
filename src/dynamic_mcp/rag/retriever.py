"""
RAG Retriever for context-aware information retrieval
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import pickle
import numpy as np
from datetime import datetime

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import chromadb
from chromadb.utils import embedding_functions

from ..core.schemas import TriggerType, RAGConfig
from ..utils.config import ConfigManager
from ..utils.text_processing import TextProcessor


class RAGRetriever:
    """
    Retrieval-Augmented Generation (RAG) system for context-aware information retrieval.
    Uses vector embeddings and semantic search to find relevant context.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.text_processor = TextProcessor()
        
        # Components
        self.embedding_model: Optional[SentenceTransformer] = None
        self.vector_store: Optional[chromadb.Collection] = None
        self.chroma_client: Optional[chromadb.Client] = None
        self._initialized = False
        
        # Cache for embeddings
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
    async def initialize(self):
        """Initialize the RAG retriever system"""
        self.logger.info("Initializing RAG Retriever")
        
        try:
            config = await self.config_manager.get_config()
            rag_config = config.rag_config
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(rag_config.embedding_model)
            
            # Initialize vector store
            await self._initialize_vector_store(rag_config)
            
            # Load existing knowledge base
            await self._load_knowledge_base()
            
            self._initialized = True
            self.logger.info("RAG Retriever initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG Retriever: {str(e)}")
            raise
    
    async def _initialize_vector_store(self, rag_config: RAGConfig):
        """Initialize ChromaDB vector store"""
        try:
            # Create vector store directory if it doesn't exist
            Path(rag_config.vector_store_path).mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=rag_config.vector_store_path
            )
            
            # Create or get collection
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=rag_config.embedding_model
            )
            
            self.vector_store = self.chroma_client.get_or_create_collection(
                name="dynamic_mcp_knowledge",
                embedding_function=embedding_function,
                metadata={"description": "Dynamic MCP knowledge base"}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {str(e)}")
            raise
    
    async def _load_knowledge_base(self):
        """Load existing knowledge base from various sources"""
        try:
            # Load from repository documentation
            await self._index_repository_docs()
            
            # Load from configuration examples
            await self._index_configuration_examples()
            
            # Load from common patterns
            await self._index_common_patterns()
            
        except Exception as e:
            self.logger.warning(f"Failed to load some knowledge base content: {str(e)}")
    
    async def _index_repository_docs(self):
        """Index documentation from the repository"""
        try:
            # Look for common documentation files
            doc_patterns = [
                "README.md",
                "docs/**/*.md",
                "*.md",
                "CHANGELOG.md",
                "CONTRIBUTING.md",
            ]
            
            # This is a simplified implementation
            # In a real system, you'd scan the repository for documentation
            sample_docs = [
                {
                    "id": "repo_readme",
                    "content": "Dynamic MCP server orchestration system with RAG/CAG capabilities",
                    "source": "README.md",
                    "type": "documentation"
                },
                {
                    "id": "migration_guide",
                    "content": "iPhone to Samsung migration guide with GitHub and AI tools optimization",
                    "source": "migration_guide.md",
                    "type": "documentation"
                }
            ]
            
            await self._add_documents_to_vector_store(sample_docs)
            
        except Exception as e:
            self.logger.warning(f"Failed to index repository docs: {str(e)}")
    
    async def _index_configuration_examples(self):
        """Index configuration examples and patterns"""
        try:
            config_examples = [
                {
                    "id": "mcp_server_config",
                    "content": "MCP server configuration with capabilities, endpoints, and routing rules",
                    "source": "config_examples",
                    "type": "configuration"
                },
                {
                    "id": "github_integration",
                    "content": "GitHub webhook integration for issue, PR, and push events",
                    "source": "config_examples",
                    "type": "configuration"
                },
                {
                    "id": "rag_configuration",
                    "content": "RAG system configuration with embedding models and vector stores",
                    "source": "config_examples",
                    "type": "configuration"
                }
            ]
            
            await self._add_documents_to_vector_store(config_examples)
            
        except Exception as e:
            self.logger.warning(f"Failed to index configuration examples: {str(e)}")
    
    async def _index_common_patterns(self):
        """Index common patterns and best practices"""
        try:
            patterns = [
                {
                    "id": "code_analysis_pattern",
                    "content": "Code analysis patterns: syntax checking, code quality, refactoring suggestions",
                    "source": "patterns",
                    "type": "pattern"
                },
                {
                    "id": "deployment_pattern",
                    "content": "Deployment patterns: CI/CD, Docker, Kubernetes, infrastructure as code",
                    "source": "patterns",
                    "type": "pattern"
                },
                {
                    "id": "testing_pattern",
                    "content": "Testing patterns: unit tests, integration tests, coverage analysis",
                    "source": "patterns",
                    "type": "pattern"
                }
            ]
            
            await self._add_documents_to_vector_store(patterns)
            
        except Exception as e:
            self.logger.warning(f"Failed to index common patterns: {str(e)}")
    
    async def _add_documents_to_vector_store(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store"""
        try:
            if not self.vector_store:
                return
            
            # Prepare documents for ChromaDB
            ids = [doc["id"] for doc in documents]
            texts = [doc["content"] for doc in documents]
            metadatas = [
                {
                    "source": doc["source"],
                    "type": doc["type"],
                    "indexed_at": datetime.now().isoformat()
                }
                for doc in documents
            ]
            
            # Add to vector store
            self.vector_store.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            self.logger.error(f"Failed to add documents to vector store: {str(e)}")
    
    async def retrieve_relevant_context(
        self, query: str, trigger_type: TriggerType, top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context documents based on query and trigger type.
        
        Args:
            query: The query text to search for
            trigger_type: Type of trigger for context filtering
            top_k: Number of top results to return
            
        Returns:
            List of relevant context documents
        """
        if not self._initialized or not self.vector_store:
            return []
        
        try:
            config = await self.config_manager.get_config()
            rag_config = config.rag_config
            
            if top_k is None:
                top_k = rag_config.top_k
            
            # Process query
            processed_query = self.text_processor.clean_text(query)
            
            # Perform semantic search
            results = self.vector_store.query(
                query_texts=[processed_query],
                n_results=top_k,
                where=self._build_filter_criteria(trigger_type)
            )
            
            # Format results
            relevant_docs = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0.0
                    
                    # Filter by similarity threshold
                    similarity = 1.0 - distance  # Convert distance to similarity
                    if similarity >= rag_config.similarity_threshold:
                        relevant_docs.append({
                            'content': doc,
                            'metadata': metadata,
                            'similarity': similarity,
                            'source': metadata.get('source', 'unknown'),
                            'type': metadata.get('type', 'unknown')
                        })
            
            self.logger.info(f"Retrieved {len(relevant_docs)} relevant documents for query")
            return relevant_docs
            
        except Exception as e:
            self.logger.error(f"Error retrieving relevant context: {str(e)}")
            return []
    
    def _build_filter_criteria(self, trigger_type: TriggerType) -> Optional[Dict[str, Any]]:
        """Build filter criteria based on trigger type"""
        # Map trigger types to relevant document types
        type_mapping = {
            TriggerType.ISSUE: ["documentation", "pattern"],
            TriggerType.PULL_REQUEST: ["pattern", "configuration"],
            TriggerType.PUSH: ["pattern", "configuration"],
            TriggerType.COMMIT: ["pattern", "configuration"],
            TriggerType.USER_PROMPT: ["documentation", "pattern", "configuration"],
            TriggerType.QUERY: ["documentation", "pattern", "configuration"],
        }
        
        relevant_types = type_mapping.get(trigger_type, ["documentation", "pattern", "configuration"])
        
        # Return None to avoid filtering for now (ChromaDB where clause can be complex)
        return None
    
    async def add_context_document(self, document: Dict[str, Any]) -> bool:
        """Add a new context document to the knowledge base"""
        try:
            if not self.vector_store:
                return False
            
            # Add single document
            await self._add_documents_to_vector_store([document])
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add context document: {str(e)}")
            return False
    
    async def update_knowledge_base(self, documents: List[Dict[str, Any]]) -> bool:
        """Update the knowledge base with new documents"""
        try:
            if not documents:
                return True
            
            await self._add_documents_to_vector_store(documents)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update knowledge base: {str(e)}")
            return False
    
    async def get_vector_store_size(self) -> int:
        """Get the number of documents in the vector store"""
        try:
            if not self.vector_store:
                return 0
            
            return self.vector_store.count()
            
        except Exception as e:
            self.logger.error(f"Error getting vector store size: {str(e)}")
            return 0
    
    def is_initialized(self) -> bool:
        """Check if the RAG retriever is initialized"""
        return self._initialized
    
    async def shutdown(self):
        """Shutdown the RAG retriever"""
        self.logger.info("Shutting down RAG Retriever")
        
        try:
            # Clear caches
            self._embedding_cache.clear()
            
            # Close vector store connection
            if self.chroma_client:
                # ChromaDB client doesn't have explicit close method
                pass
            
            self._initialized = False
            self.logger.info("RAG Retriever shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during RAG Retriever shutdown: {str(e)}")
            raise