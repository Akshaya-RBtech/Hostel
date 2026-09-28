"""
Lightweight RAG (Retrieval-Augmented Generation) Service for WasteZero
=====================================================================
Implements a simple TF-IDF + Cosine Similarity based retrieval index
using only numpy and built-in Python. No external vector DB required.

Used to retrieve relevant feedback/context before sending to Gemini LLM.
"""

import re
import math
import numpy as np
from collections import Counter


class RAGIndex:
    """Simple TF-IDF based retrieval index for RAG."""
    
    def __init__(self):
        self.documents = []
        self.tfidf_matrix = None
        self.vocab = []
        self.word_to_idx = {}
        self.is_built = False
    
    def build_index(self, records):
        """
        Build the TF-IDF index from a list of feedback/context records.
        Each record should have at minimum a text field (e.g., 'reason', 'dish', etc.).
        """
        self.documents = []
        texts = []
        
        for record in records:
            # Build searchable text from record fields
            parts = []
            if isinstance(record, dict):
                for key in ['reason', 'dish', 'student_id', 'items', 'meal_type', 'date']:
                    if key in record and record[key]:
                        parts.append(str(record[key]))
            elif isinstance(record, str):
                parts.append(record)
            
            text = ' '.join(parts)
            if text.strip():
                self.documents.append({'text': text, 'record': record})
                texts.append(text)
        
        if not texts:
            self.is_built = False
            return
        
        # Compute TF-IDF
        self.tfidf_matrix, self.vocab = self._compute_tfidf(texts)
        self.word_to_idx = {w: i for i, w in enumerate(self.vocab)}
        self.is_built = len(self.vocab) > 0 and len(texts) > 0
    
    def retrieve(self, query, top_k=5):
        """
        Retrieve the top-k most relevant documents for a given query.
        Returns list of dicts with 'text', 'score', and 'record'.
        """
        if not self.is_built or not self.documents:
            return []
        
        # Get query TF-IDF vector
        query_vector = self._query_to_vector(query)
        
        if query_vector is None or np.all(query_vector == 0):
            return []
        
        # Compute cosine similarity with all documents
        scores = []
        for i in range(len(self.documents)):
            doc_vector = self.tfidf_matrix[i]
            similarity = self._cosine_similarity(query_vector, doc_vector)
            scores.append((i, similarity))
        
        # Sort by similarity score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results with score > 0
        results = []
        for idx, score in scores[:top_k]:
            if score > 0.01:  # Minimum relevance threshold
                results.append({
                    'text': self.documents[idx]['text'],
                    'score': float(score),
                    'record': self.documents[idx]['record']
                })
        
        return results
    
    def _compute_tfidf(self, documents):
        """Compute TF-IDF matrix from scratch."""
        # Tokenize
        tokenized = []
        for doc in documents:
            tokens = re.findall(r'\b[a-zA-Z]{2,}\b', doc.lower())
            tokenized.append(tokens)
        
        # Build vocabulary
        vocab = sorted(set(word for doc in tokenized for word in doc))
        if not vocab:
            return np.array([]), []
        
        word_to_idx = {w: i for i, w in enumerate(vocab)}
        n_docs = len(tokenized)
        n_words = len(vocab)
        
        # Compute TF
        tf = np.zeros((n_docs, n_words))
        for i, doc in enumerate(tokenized):
            counter = Counter(doc)
            total = len(doc) if doc else 1
            for word, count in counter.items():
                if word in word_to_idx:
                    tf[i][word_to_idx[word]] = count / total
        
        # Compute IDF
        idf = np.zeros(n_words)
        for j in range(n_words):
            doc_count = sum(1 for i in range(n_docs) if tf[i][j] > 0)
            idf[j] = math.log((n_docs + 1) / (doc_count + 1)) + 1
        
        tfidf = tf * idf
        return tfidf, vocab
    
    def _query_to_vector(self, query):
        """Convert a query string to a TF-IDF vector using the existing vocabulary."""
        if not self.vocab:
            return None
        
        tokens = re.findall(r'\b[a-zA-Z]{2,}\b', query.lower())
        if not tokens:
            return None
        
        vector = np.zeros(len(self.vocab))
        counter = Counter(tokens)
        total = len(tokens)
        
        for word, count in counter.items():
            if word in self.word_to_idx:
                vector[self.word_to_idx[word]] = count / total
        
        return vector
    
    @staticmethod
    def _cosine_similarity(a, b):
        """Compute cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# Singleton RAG index instance
rag_index = RAGIndex()
