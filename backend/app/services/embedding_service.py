"""
Embedding service for generating text embeddings using OpenAI-compatible APIs.
"""

from openai import OpenAI
from typing import List, Union
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.models.model_config import get_embedding_config, is_embedding_configured


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        """Initialize the embedding service."""
        self.client = None
        self.model_id = None
        self.dimension = None
        self._load_config()
    
    def _load_config(self):
        """Load embedding configuration."""
        if not is_embedding_configured():
            return
        
        config = get_embedding_config()
        self.client = OpenAI(
            api_key=config['api_key'],
            base_url=config['api_url']
        )
        self.model_id = config['model_id']
        self.dimension = config.get('dimension', 2560)
    
    def is_available(self) -> bool:
        """Check if embedding service is available."""
        return self.client is not None and self.model_id is not None
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.dimension
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            RuntimeError: If embedding service is not configured
        """
        if not self.is_available():
            raise RuntimeError("Embedding service is not configured")
        
        response = self.client.embeddings.create(
            model=self.model_id,
            input=text,
            encoding_format="float"
        )
        
        return response.data[0].embedding
    
    def embed_texts(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to embed in a single API call
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If embedding service is not configured
        """
        if not self.is_available():
            raise RuntimeError("Embedding service is not configured")
        
        if not texts:
            return []
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            response = self.client.embeddings.create(
                model=self.model_id,
                input=batch,
                encoding_format="float"
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings


_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def reload_embedding_service():
    """Reload the embedding service with new configuration."""
    global _embedding_service
    _embedding_service = EmbeddingService()
    return _embedding_service
