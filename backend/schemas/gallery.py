from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PhotoUploadResponse(BaseModel):
    id: int
    filename: str
    faces_count: int
    faces: List[dict]
    
class FaceCreate(BaseModel):
    photo_id: int
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    confidence: float
    embedding_vector: str
    
class PersonCreate(BaseModel):
    name: str
    
class PersonUpdate(BaseModel):
    name: str
    
class PersonResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
class FaceResponse(BaseModel):
    id: int
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    confidence: float
    person: Optional[PersonResponse]
    is_verified: bool
    
class PhotoResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    faces_count: int
    faces: List[FaceResponse]
    created_at: datetime
    
class GalleryResponse(BaseModel):
    photos: List[PhotoResponse]
    total: int
    
class FaceAssignRequest(BaseModel):
    person_id: Optional[int] = None
    new_person_name: Optional[str] = None