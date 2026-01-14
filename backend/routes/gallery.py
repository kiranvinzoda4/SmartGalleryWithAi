from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import json
import numpy as np
from PIL import Image

from connection import get_db
from models import User, Photo, Person, Face
from schemas.gallery import *
from services.gallery_face_service import GalleryFaceService
from utils.auth import get_current_user

router = APIRouter(prefix="/gallery", tags=["gallery"])

# Try to initialize face service, but don't fail if it errors
try:
    face_service = GalleryFaceService()
    print("✓ Face recognition service initialized")
except Exception as e:
    print(f"⚠ Face recognition not available: {e}")
    face_service = None

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload photo and detect faces"""
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        # Save file
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Get image dimensions
        try:
            with Image.open(file_path) as img:
                width, height = img.size
        except:
            width, height = None, None
        
        # Detect faces
        faces_data = []
        if face_service:
            try:
                faces_data = face_service.detect_faces_in_photo(file_path)
            except Exception as face_err:
                print(f"Face detection error: {face_err}")
        else:
            print("Face service not available, skipping face detection")
        
        # Create photo record
        photo = Photo(
            user_id=current_user.id,
            filename=filename,
            original_name=file.filename,
            file_path=file_path,
            file_size=len(content),
            width=width,
            height=height,
            faces_count=len(faces_data)
        )
        db.add(photo)
        db.flush()
        
        # Create face records
        faces = []
        if face_service:
            for face_data in faces_data:
                try:
                    embedding = np.array(face_data['embedding'])
                    person_match = face_service.search_person(embedding)
                    
                    face = Face(
                        photo_id=photo.id,
                        person_id=person_match['person_id'] if person_match else None,
                        bbox_x=face_data['bbox']['x'],
                        bbox_y=face_data['bbox']['y'],
                        bbox_width=face_data['bbox']['width'],
                        bbox_height=face_data['bbox']['height'],
                        confidence=face_data['confidence'],
                        embedding_vector=json.dumps(face_data['embedding']),
                        is_verified=bool(person_match)
                    )
                    db.add(face)
                    faces.append(face)
                except Exception as face_err:
                    print(f"Face record error: {face_err}")
                    continue
        
        db.commit()
        
        return {
            'id': photo.id,
            'filename': filename,
            'faces_count': len(faces_data),
            'faces': [{
                'id': f.id,
                'bbox': {'x': f.bbox_x, 'y': f.bbox_y, 'width': f.bbox_width, 'height': f.bbox_height},
                'confidence': f.confidence,
                'person_id': f.person_id,
                'is_verified': f.is_verified
            } for f in faces]
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = traceback.format_exc()
        print(f"Upload error: {error_detail}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.get("/photos")
def get_photos(
    person_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's photos with optional person filter"""
    try:
        query = db.query(Photo).filter(Photo.user_id == current_user.id)
        
        if person_id:
            query = query.join(Face).filter(Face.person_id == person_id)
        
        total = query.count()
        photos = query.order_by(Photo.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for photo in photos:
            faces_list = []
            for face in photo.faces:
                face_dict = {
                    'id': face.id,
                    'bbox_x': face.bbox_x,
                    'bbox_y': face.bbox_y,
                    'bbox_width': face.bbox_width,
                    'bbox_height': face.bbox_height,
                    'confidence': face.confidence,
                    'is_verified': face.is_verified,
                    'person': None
                }
                if face.person_id:
                    person = db.query(Person).filter(Person.id == face.person_id).first()
                    if person:
                        face_dict['person'] = {
                            'id': person.id,
                            'name': person.name,
                            'created_at': person.created_at
                        }
                faces_list.append(face_dict)
            
            result.append({
                'id': photo.id,
                'filename': photo.filename,
                'original_name': photo.original_name,
                'file_size': photo.file_size,
                'width': photo.width,
                'height': photo.height,
                'faces_count': photo.faces_count,
                'faces': faces_list,
                'created_at': photo.created_at
            })
        
        return {'photos': result, 'total': total}
    except Exception as e:
        print(f"Get photos error: {str(e)}")
        raise HTTPException(500, f"Failed to get photos: {str(e)}")

@router.post("/faces/{face_id}/assign")
def assign_face_to_person(
    face_id: int,
    request: FaceAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign face to existing person or create new person"""
    if not request.new_person_name and not request.person_id:
        raise HTTPException(400, "Either new_person_name or person_id must be provided")
    
    face = db.query(Face).join(Photo).filter(
        Face.id == face_id,
        Photo.user_id == current_user.id
    ).first()
    
    if not face:
        raise HTTPException(404, "Face not found")
    
    embedding = np.array(json.loads(face.embedding_vector))
    
    if request.new_person_name:
        if not face_service:
            raise HTTPException(503, "Face recognition service not available")
        
        embedding_id = face_service.add_person(request.new_person_name, embedding, current_user.id)
        
        person = Person(
            user_id=current_user.id,
            name=request.new_person_name,
            face_embedding_id=embedding_id
        )
        db.add(person)
        db.flush()
        
        face_service.update_person_mapping(embedding_id, person.id)
        face.person_id = person.id
        
    elif request.person_id:
        person = db.query(Person).filter(
            Person.id == request.person_id,
            Person.user_id == current_user.id
        ).first()
        
        if not person:
            raise HTTPException(404, "Person not found")
        
        if face_service:
            face_service.update_person_embedding(person.id, embedding)
        
        face.person_id = person.id
    
    face.is_verified = True
    db.commit()
    
    return {"message": "Face assigned successfully"}

@router.get("/persons")
def get_persons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all persons for current user"""
    try:
        persons = db.query(Person).filter(Person.user_id == current_user.id).all()
        return [{
            'id': p.id,
            'name': p.name,
            'created_at': p.created_at
        } for p in persons]
    except Exception as e:
        print(f"Get persons error: {str(e)}")
        raise HTTPException(500, f"Failed to get persons: {str(e)}")

@router.put("/persons/{person_id}")
def update_person(
    person_id: int,
    request: PersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update person name"""
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not person:
        raise HTTPException(404, "Person not found")
    
    person.name = request.name
    db.commit()
    
    return {"message": "Person updated successfully"}

@router.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete photo and its file"""
    photo = db.query(Photo).filter(
        Photo.id == photo_id,
        Photo.user_id == current_user.id
    ).first()
    
    if not photo:
        raise HTTPException(404, "Photo not found")
    
    # Delete file
    if os.path.exists(photo.file_path):
        os.remove(photo.file_path)
    
    # Delete from database (faces cascade delete)
    db.delete(photo)
    db.commit()
    
    return {"message": "Photo deleted successfully"}

@router.delete("/persons/{person_id}")
def delete_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete person and unassign all faces"""
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not person:
        raise HTTPException(404, "Person not found")
    
    # Unassign all faces
    db.query(Face).filter(Face.person_id == person_id).update({
        'person_id': None,
        'is_verified': False
    })
    
    # Remove from face service
    face_service.delete_person(person_id)
    
    # Delete person
    db.delete(person)
    db.commit()
    
    return {"message": "Person deleted successfully"}