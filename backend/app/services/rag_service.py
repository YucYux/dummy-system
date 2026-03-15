"""
RAG (Retrieval-Augmented Generation) service.
Handles text chunking, embedding, vector storage and retrieval.
"""

import os
import pickle
import numpy as np
import tiktoken
from typing import List, Dict, Any, Optional, Tuple
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from app.services.embedding_service import get_embedding_service, reload_embedding_service
from app.models.doc_library import (
    get_library_dir, get_library_chunks, get_chunks_by_ids,
    add_chunks, update_document_status, update_library_stats,
    get_library, get_document
)
from app.models.model_config import get_embedding_config

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class TextChunker:
    """Text chunker with configurable parameters."""
    
    def __init__(self, 
                 default_chunk_size: int = None,
                 min_chunk_size: int = None,
                 chunk_overlap: int = None,
                 delimiters: List[str] = None):
        """
        Initialize the text chunker.
        
        Args:
            default_chunk_size: Target chunk size in tokens
            min_chunk_size: Minimum chunk size (won't split even if delimiter found)
            chunk_overlap: Overlap between chunks in tokens
            delimiters: List of delimiters to split on (in priority order)
        """
        self.default_chunk_size = default_chunk_size or config.RAG_DEFAULT_CHUNK_SIZE
        self.min_chunk_size = min_chunk_size or config.RAG_MIN_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.RAG_CHUNK_OVERLAP
        self.delimiters = delimiters or config.RAG_CHUNK_DELIMITERS
        
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text."""
        return len(self.tokenizer.encode(text))
    
    def _find_split_point(self, text: str, start: int, target_end: int) -> int:
        """
        Find the best split point in the text.
        Returns the character index to split at.
        """
        search_text = text[start:target_end]
        
        for delimiter in self.delimiters:
            last_pos = search_text.rfind(delimiter)
            if last_pos != -1:
                split_pos = start + last_pos + len(delimiter)
                chunk_text = text[start:split_pos]
                if self.count_tokens(chunk_text) >= self.min_chunk_size:
                    return split_pos
        
        return target_end
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks.
        
        Returns:
            List of chunk dictionaries with:
            - index: chunk index
            - content: chunk text
            - token_count: number of tokens
            - start_char: start character position
            - end_char: end character position
        """
        if not text.strip():
            return []
        
        chunks = []
        text_len = len(text)
        pos = 0
        chunk_index = 0
        
        while pos < text_len:
            chunk_tokens = self.tokenizer.encode(text[pos:])
            
            if len(chunk_tokens) <= self.default_chunk_size:
                chunk_content = text[pos:].strip()
                if chunk_content:
                    chunks.append({
                        'index': chunk_index,
                        'content': chunk_content,
                        'token_count': len(chunk_tokens),
                        'start_char': pos,
                        'end_char': text_len
                    })
                break
            
            target_tokens = chunk_tokens[:self.default_chunk_size]
            target_text = self.tokenizer.decode(target_tokens)
            target_end = pos + len(target_text)
            
            split_pos = self._find_split_point(text, pos, min(target_end, text_len))
            
            chunk_content = text[pos:split_pos].strip()
            if chunk_content:
                chunks.append({
                    'index': chunk_index,
                    'content': chunk_content,
                    'token_count': self.count_tokens(chunk_content),
                    'start_char': pos,
                    'end_char': split_pos
                })
                chunk_index += 1
            
            overlap_tokens = chunk_tokens[:self.chunk_overlap] if self.chunk_overlap > 0 else []
            if overlap_tokens and split_pos < text_len:
                overlap_text = self.tokenizer.decode(overlap_tokens)
                next_start = split_pos - len(overlap_text)
                pos = max(next_start, split_pos - self.chunk_overlap * 4)
            else:
                pos = split_pos
            
            if pos >= text_len:
                break
        
        return chunks


class FAISSIndex:
    """FAISS index wrapper for vector storage and retrieval."""
    
    def __init__(self, dimension: int):
        """
        Initialize FAISS index.
        
        Args:
            dimension: Dimension of the embedding vectors
        """
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS is not installed. Please install faiss-cpu.")
        
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.chunk_ids = []
    
    def add(self, embeddings: List[List[float]], chunk_ids: List[str]):
        """
        Add embeddings to the index.
        
        Args:
            embeddings: List of embedding vectors
            chunk_ids: List of chunk IDs corresponding to embeddings
        """
        if not embeddings:
            return
        
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        
        self.index.add(vectors)
        self.chunk_ids.extend(chunk_ids)
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            
        Returns:
            List of (chunk_id, score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        query_vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vector)
        
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.chunk_ids):
                results.append((self.chunk_ids[idx], float(scores[0][i])))
        
        return results
    
    def remove(self, chunk_ids_to_remove: List[str]):
        """
        Remove chunks from the index.
        This rebuilds the index without the specified chunks.
        """
        if not chunk_ids_to_remove:
            return
        
        remove_set = set(chunk_ids_to_remove)
        keep_indices = [i for i, cid in enumerate(self.chunk_ids) if cid not in remove_set]
        
        if not keep_indices:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.chunk_ids = []
            return
        
        vectors = np.zeros((len(keep_indices), self.dimension), dtype=np.float32)
        for new_idx, old_idx in enumerate(keep_indices):
            vectors[new_idx] = self.index.reconstruct(old_idx)
        
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(vectors)
        self.chunk_ids = [self.chunk_ids[i] for i in keep_indices]
    
    def save(self, path: str):
        """Save index to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(self.index, path + ".faiss")
        with open(path + ".ids", 'wb') as f:
            pickle.dump(self.chunk_ids, f)
    
    @classmethod
    def load(cls, path: str, dimension: int) -> 'FAISSIndex':
        """Load index from disk."""
        instance = cls(dimension)
        
        faiss_path = path + ".faiss"
        ids_path = path + ".ids"
        
        if os.path.exists(faiss_path) and os.path.exists(ids_path):
            instance.index = faiss.read_index(faiss_path)
            with open(ids_path, 'rb') as f:
                instance.chunk_ids = pickle.load(f)
        
        return instance


class RAGService:
    """Main RAG service for document processing and retrieval."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.chunker = TextChunker()
        self._library_indexes: Dict[str, FAISSIndex] = {}
    
    def _get_index_path(self, user_id: str, library_id: str) -> str:
        """Get the path to a library's FAISS index."""
        return os.path.join(get_library_dir(user_id, library_id), "index")
    
    def _get_or_load_index(self, user_id: str, library_id: str) -> FAISSIndex:
        """Get or load the FAISS index for a library."""
        cache_key = f"{user_id}:{library_id}"
        
        if cache_key in self._library_indexes:
            return self._library_indexes[cache_key]
        
        embedding_config = get_embedding_config()
        dimension = embedding_config.get('dimension', 2560)
        
        index_path = self._get_index_path(user_id, library_id)
        index = FAISSIndex.load(index_path, dimension)
        
        self._library_indexes[cache_key] = index
        return index
    
    def _save_index(self, user_id: str, library_id: str, index: FAISSIndex):
        """Save a library's FAISS index."""
        index_path = self._get_index_path(user_id, library_id)
        index.save(index_path)
        
        cache_key = f"{user_id}:{library_id}"
        self._library_indexes[cache_key] = index
    
    def invalidate_index_cache(self, user_id: str, library_id: str):
        """Invalidate cached index for a library."""
        cache_key = f"{user_id}:{library_id}"
        if cache_key in self._library_indexes:
            del self._library_indexes[cache_key]
    
    def process_document(self, user_id: str, library_id: str, doc_id: str, 
                         file_path: str, progress_callback=None) -> bool:
        """
        Process a document: read, chunk, embed, and index.
        
        Args:
            user_id: User ID
            library_id: Library ID
            doc_id: Document ID
            file_path: Path to the document file
            progress_callback: Optional callback function(progress: float)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_document_status(user_id, doc_id, 'processing')
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if progress_callback:
                progress_callback(0.1)
            
            chunks = self.chunker.chunk_text(content)
            
            if not chunks:
                update_document_status(user_id, doc_id, 'completed', 
                                       token_count=0, chunk_count=0)
                return True
            
            if progress_callback:
                progress_callback(0.2)
            
            total_tokens = sum(c['token_count'] for c in chunks)
            
            add_chunks(user_id, doc_id, library_id, chunks)
            
            if progress_callback:
                progress_callback(0.3)
            
            embedding_service = get_embedding_service()
            if not embedding_service.is_available():
                raise RuntimeError("Embedding service not available")
            
            chunk_texts = [c['content'] for c in chunks]
            
            all_embeddings = []
            batch_size = 20
            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i:i + batch_size]
                batch_embeddings = embedding_service.embed_texts(batch)
                all_embeddings.extend(batch_embeddings)
                
                if progress_callback:
                    progress = 0.3 + 0.6 * (i + len(batch)) / len(chunk_texts)
                    progress_callback(progress)
            
            db_chunks = get_library_chunks(user_id, library_id)
            doc_chunk_ids = [c['id'] for c in db_chunks if c['document_id'] == doc_id]
            
            index = self._get_or_load_index(user_id, library_id)
            index.add(all_embeddings, doc_chunk_ids)
            self._save_index(user_id, library_id, index)
            
            if progress_callback:
                progress_callback(0.95)
            
            update_document_status(user_id, doc_id, 'completed',
                                   token_count=total_tokens, chunk_count=len(chunks))
            update_library_stats(user_id, library_id)
            
            if progress_callback:
                progress_callback(1.0)
            
            return True
            
        except Exception as e:
            update_document_status(user_id, doc_id, 'failed', error_message=str(e))
            return False
    
    def remove_document_from_index(self, user_id: str, library_id: str, doc_id: str):
        """Remove a document's chunks from the FAISS index."""
        chunks = get_library_chunks(user_id, library_id)
        chunk_ids_to_remove = [c['id'] for c in chunks if c['document_id'] == doc_id]
        
        if chunk_ids_to_remove:
            index = self._get_or_load_index(user_id, library_id)
            index.remove(chunk_ids_to_remove)
            self._save_index(user_id, library_id, index)
    
    def search(self, user_id: str, library_ids: List[str], query: str, 
               top_k: int = None) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks across multiple libraries.
        
        Args:
            user_id: User ID
            library_ids: List of library IDs to search
            query: Search query
            top_k: Number of results to return (uses config default if not specified)
            
        Returns:
            List of chunk dictionaries with relevance scores
        """
        if top_k is None:
            top_k = config.RAG_TOP_K
        
        embedding_service = get_embedding_service()
        if not embedding_service.is_available():
            raise RuntimeError("Embedding service not available")
        
        query_embedding = embedding_service.embed_text(query)
        
        all_results = []
        
        for library_id in library_ids:
            library = get_library(user_id, library_id)
            if not library or library.get('status') != 'ready':
                continue
            
            index = self._get_or_load_index(user_id, library_id)
            results = index.search(query_embedding, top_k * 2)
            
            for chunk_id, score in results:
                all_results.append({
                    'chunk_id': chunk_id,
                    'library_id': library_id,
                    'score': score
                })
        
        all_results.sort(key=lambda x: x['score'], reverse=True)
        top_results = all_results[:top_k]
        
        chunk_ids = [r['chunk_id'] for r in top_results]
        chunks = get_chunks_by_ids(user_id, chunk_ids)
        chunk_map = {c['id']: c for c in chunks}
        
        final_results = []
        for result in top_results:
            chunk = chunk_map.get(result['chunk_id'])
            if chunk:
                final_results.append({
                    'content': chunk['content'],
                    'source': chunk['original_filename'],
                    'library_id': result['library_id'],
                    'score': result['score'],
                    'token_count': chunk['token_count']
                })
        
        return final_results
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text."""
        return self.chunker.count_tokens(text)


_rag_service = None


def get_rag_service() -> RAGService:
    """Get the singleton RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
