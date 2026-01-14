import cv2
import numpy as np
import os
import faiss
import pickle
import json
import uuid
from typing import List, Dict, Tuple, Optional
from insightface.app import FaceAnalysis
from PIL import Image

class GalleryFaceService:
    def __init__(self):
        self.app = FaceAnalysis(providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        self.embedding_dim = 512
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.person_mappings = {}
        
        self.load_index()
        
    def detect_faces_in_photo(self, image_path: str) -> List[Dict]:
        """Detect all faces in a photo and return face data"""
        image = cv2.imread(image_path)
        if image is None:
            return []
            
        faces = self.app.get(image)
        face_data = []
        
        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            
            face_info = {
                'bbox': {
                    'x': float(x1),
                    'y': float(y1), 
                    'width': float(x2 - x1),
                    'height': float(y2 - y1)
                },
                'confidence': float(face.det_score),
                'embedding': face.embedding.tolist()
            }
            face_data.append(face_info)
            
        return face_data
    
    def search_person(self, embedding: np.ndarray, threshold: float = 0.7) -> Optional[Dict]:
        """Search for matching person using face embedding"""
        if self.index.ntotal == 0:
            return None
            
        query_norm = embedding / np.linalg.norm(embedding)
        distances, indices = self.index.search(query_norm.reshape(1, -1), 1)
        
        if len(distances[0]) > 0:
            distance = distances[0][0]
            idx = indices[0][0]
            
            similarity = 1 - (distance * distance / 2)
            similarity = max(0, min(1, similarity))
            
            if similarity >= threshold and idx in self.person_mappings:
                result = self.person_mappings[idx].copy()
                result['similarity'] = float(similarity)
                return result
                
        return None
    
    def add_person(self, name: str, embedding: np.ndarray, user_id: int) -> str:
        """Add new person to the face index"""
        embedding_id = str(uuid.uuid4())
        
        embedding_norm = embedding / np.linalg.norm(embedding)
        current_index = self.index.ntotal
        self.index.add(embedding_norm.reshape(1, -1))
        
        self.person_mappings[current_index] = {
            'person_id': None,  # Will be set after DB insert
            'name': name,
            'embedding_id': embedding_id,
            'user_id': user_id
        }
        
        self.save_index()
        return embedding_id
    
    def update_person_mapping(self, embedding_id: str, person_id: int):
        """Update person mapping with database ID"""
        for idx, mapping in self.person_mappings.items():
            if mapping['embedding_id'] == embedding_id:
                mapping['person_id'] = person_id
                break
        self.save_index()
    
    def delete_person(self, person_id: int):
        """Remove person from face index"""
        index_to_remove = None
        for idx, mapping in self.person_mappings.items():
            if mapping.get('person_id') == person_id:
                index_to_remove = idx
                break
                
        if index_to_remove is not None:
            del self.person_mappings[index_to_remove]
            self.rebuild_index()
    
    def update_person_embedding(self, person_id: int, new_embedding: np.ndarray):
        """Update person embedding by averaging with new face (improves recognition)"""
        for idx, mapping in self.person_mappings.items():
            if mapping.get('person_id') == person_id:
                # Get current embedding
                current_embedding = self.index.reconstruct(idx)
                
                # Average with new embedding
                new_embedding_norm = new_embedding / np.linalg.norm(new_embedding)
                averaged = (current_embedding + new_embedding_norm) / 2
                averaged = averaged / np.linalg.norm(averaged)
                
                # Update in index
                self.index = self._replace_embedding_at_index(idx, averaged)
                self.save_index()
                break
    
    def _replace_embedding_at_index(self, idx: int, new_embedding: np.ndarray):
        """Replace embedding at specific index"""
        new_index = faiss.IndexFlatL2(self.embedding_dim)
        new_mappings = {}
        
        for old_idx, mapping in self.person_mappings.items():
            if old_idx < self.index.ntotal:
                if old_idx == idx:
                    embedding = new_embedding
                else:
                    embedding = self.index.reconstruct(old_idx)
                
                new_idx = new_index.ntotal
                new_index.add(embedding.reshape(1, -1))
                new_mappings[new_idx] = mapping
        
        self.person_mappings = new_mappings
        return new_index
    
    def rebuild_index(self):
        """Rebuild FAISS index after deletion"""
        new_index = faiss.IndexFlatL2(self.embedding_dim)
        new_mappings = {}
        
        for old_idx, mapping in self.person_mappings.items():
            if old_idx < self.index.ntotal:
                embedding = self.index.reconstruct(old_idx)
                new_idx = new_index.ntotal
                new_index.add(embedding.reshape(1, -1))
                new_mappings[new_idx] = mapping
        
        self.index = new_index
        self.person_mappings = new_mappings
        self.save_index()
    
    def save_index(self):
        """Save FAISS index and mappings"""
        os.makedirs("./gallery_index", exist_ok=True)
        faiss.write_index(self.index, "./gallery_index/person_embeddings.index")
        
        with open("./gallery_index/person_mappings.pkl", "wb") as f:
            pickle.dump(self.person_mappings, f)
    
    def load_index(self):
        """Load FAISS index and mappings"""
        try:
            if os.path.exists("./gallery_index/person_embeddings.index"):
                self.index = faiss.read_index("./gallery_index/person_embeddings.index")
                
            if os.path.exists("./gallery_index/person_mappings.pkl"):
                with open("./gallery_index/person_mappings.pkl", "rb") as f:
                    self.person_mappings = pickle.load(f)
        except Exception as e:
            print(f"Error loading index: {e}")
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.person_mappings = {}