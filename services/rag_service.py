import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LocalRAGIndex:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.documents = []
        self.doc_metadata = []
        self.tfidf_matrix = None
        self.is_built = False

    def build_index(self, feedbacks):
        """
        Builds a TF-IDF semantic search index out of textual feedback data.
        feedbacks is a list of dicts: [{'reason': '...', 'dish': '...', 'time': '...'}]
        """
        self.documents = []
        self.doc_metadata = []
        
        for f in feedbacks:
            if f.get('reason') and str(f['reason']).strip():
                # Combine dish and reason for better semantic matching
                text = f"Feedback about {f.get('dish', 'unknown meal')}: {f['reason']}"
                self.documents.append(text)
                self.doc_metadata.append(f)
                
        if self.documents:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            self.is_built = True
        else:
            self.is_built = False

    def retrieve(self, query, top_k=5):
        """Retrieves top_k most similar feedback strings for the query."""
        if not self.is_built or not self.documents:
            return []
            
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get indices of top_k matched scores > 0
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.05:  # threshold
                results.append({
                    'score': similarities[idx],
                    'text': self.documents[idx],
                    'metadata': self.doc_metadata[idx]
                })
        return results

rag_index = LocalRAGIndex()
