'use client'

import { useState, useEffect } from 'react'
import { Container, Box, Button, Grid, Card, CardMedia, Typography, Dialog, DialogTitle, DialogContent, TextField, Select, MenuItem, FormControl, InputLabel, Chip, IconButton, CircularProgress } from '@mui/material'
import { CloudUpload, Person, Close, Label, LabelOff } from '@mui/icons-material'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

export default function GalleryPage() {
  const [photos, setPhotos] = useState([])
  const [persons, setPersons] = useState([])
  const [selectedPhoto, setSelectedPhoto] = useState(null)
  const [selectedFace, setSelectedFace] = useState(null)
  const [newPersonName, setNewPersonName] = useState('')
  const [selectedPersonId, setSelectedPersonId] = useState('')
  const [filterPersonId, setFilterPersonId] = useState('')
  const [loading, setLoading] = useState(false)
  const [showNames, setShowNames] = useState(true)

  useEffect(() => {
    loadPhotos()
    loadPersons()
  }, [filterPersonId])

  const loadPhotos = async () => {
    try {
      const token = localStorage.getItem('token')
      const url = filterPersonId ? `${API_URL}/gallery/photos?person_id=${filterPersonId}` : `${API_URL}/gallery/photos`
      const res = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } })
      setPhotos(res.data.photos || [])
    } catch (err) {
      console.error('Load photos error:', err)
      setPhotos([])
    }
  }

  const loadPersons = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await axios.get(`${API_URL}/gallery/persons`, { headers: { Authorization: `Bearer ${token}` } })
      setPersons(res.data || [])
    } catch (err) {
      console.error('Load persons error:', err)
      setPersons([])
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const token = localStorage.getItem('token')
      await axios.post(`${API_URL}/gallery/upload`, formData, { headers: { Authorization: `Bearer ${token}` } })
      loadPhotos()
      loadPersons()
    } catch (err) {
      alert('Upload failed')
    }
    setLoading(false)
  }

  const handleAssignFace = async () => {
    try {
      const token = localStorage.getItem('token')
      const data = newPersonName ? { new_person_name: newPersonName } : { person_id: parseInt(selectedPersonId) }
      await axios.post(`${API_URL}/gallery/faces/${selectedFace.id}/assign`, data, { headers: { Authorization: `Bearer ${token}` } })
      setSelectedFace(null)
      setNewPersonName('')
      setSelectedPersonId('')
      loadPhotos()
      loadPersons()
    } catch (err) {
      alert('Assignment failed')
    }
  }

  const handleDeletePhoto = async (photoId) => {
    if (!confirm('Delete this photo?')) return
    try {
      const token = localStorage.getItem('token')
      await axios.delete(`${API_URL}/gallery/photos/${photoId}`, { headers: { Authorization: `Bearer ${token}` } })
      loadPhotos()
    } catch (err) {
      alert('Delete failed')
    }
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Typography variant="h4">My Gallery</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Filter by Person</InputLabel>
            <Select value={filterPersonId} onChange={(e) => setFilterPersonId(e.target.value)} label="Filter by Person">
              <MenuItem value="">All Photos</MenuItem>
              {persons.map(p => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
            </Select>
          </FormControl>
          <Button variant="contained" component="label" startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />} disabled={loading}>
            Upload Photo
            <input type="file" hidden accept="image/*" onChange={handleUpload} />
          </Button>
        </Box>
      </Box>

      <Grid container spacing={2}>
        {photos.length === 0 ? (
          <Grid item xs={12}>
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No photos yet
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Upload your first photo to get started!
              </Typography>
            </Box>
          </Grid>
        ) : (
          photos.map(photo => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={photo.id}>
              <Card sx={{ cursor: 'pointer', position: 'relative' }}>
                <CardMedia component="img" height="200" image={`${API_URL}/uploads/${photo.filename}`} onClick={() => setSelectedPhoto(photo)} />
                <IconButton
                  onClick={(e) => { e.stopPropagation(); handleDeletePhoto(photo.id); }}
                  sx={{ position: 'absolute', top: 8, right: 8, bgcolor: 'rgba(255,255,255,0.8)', '&:hover': { bgcolor: 'rgba(255,0,0,0.8)', color: 'white' } }}
                >
                  <Close />
                </IconButton>
                <Box sx={{ p: 1 }}>
                  <Typography variant="caption">{photo.faces_count} faces</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                    {photo.faces?.filter(f => f.person).map(f => (
                      <Chip key={f.id} label={f.person.name} size="small" />
                    ))}
                  </Box>
                </Box>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      <Dialog open={!!selectedPhoto} onClose={() => setSelectedPhoto(null)} maxWidth="md" fullWidth>
        <DialogTitle>
          Photo Details
          <IconButton onClick={() => setShowNames(!showNames)} sx={{ position: 'absolute', right: 48, top: 8 }}>
            {showNames ? <Label /> : <LabelOff />}
          </IconButton>
          <IconButton onClick={() => setSelectedPhoto(null)} sx={{ position: 'absolute', right: 8, top: 8 }}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedPhoto && (
            <>
              <Box sx={{ position: 'relative', mb: 2 }}>
                <img src={`${API_URL}/uploads/${selectedPhoto.filename}`} style={{ width: '100%' }} />
                {showNames && selectedPhoto.faces?.map(face => (
                  <Box
                    key={face.id}
                    onClick={() => !face.person && setSelectedFace(face)}
                    sx={{
                      position: 'absolute',
                      left: `${(face.bbox_x / selectedPhoto.width) * 100}%`,
                      top: `${(face.bbox_y / selectedPhoto.height) * 100}%`,
                      width: `${(face.bbox_width / selectedPhoto.width) * 100}%`,
                      height: `${(face.bbox_height / selectedPhoto.height) * 100}%`,
                      border: face.person ? '3px solid #4caf50' : '3px solid #f44336',
                      cursor: face.person ? 'default' : 'pointer',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' }
                    }}
                  >
                    {face.person && (
                      <Box sx={{ 
                        position: 'absolute', 
                        bottom: -30, 
                        left: '50%', 
                        transform: 'translateX(-50%)',
                        bgcolor: '#4caf50',
                        color: 'white',
                        px: 2,
                        py: 0.5,
                        borderRadius: 2,
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        whiteSpace: 'nowrap',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
                      }}>
                        {face.person.name}
                      </Box>
                    )}
                  </Box>
                ))}
              </Box>
              <Typography variant="body2" color="text.secondary">
                Click red boxes to name unknown faces
              </Typography>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={!!selectedFace} onClose={() => setSelectedFace(null)}>
        <DialogTitle>Name This Face</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="New Person Name"
            value={newPersonName}
            onChange={(e) => setNewPersonName(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
          />
          <Typography align="center" sx={{ my: 2 }}>OR</Typography>
          <FormControl fullWidth>
            <InputLabel>Select Existing Person</InputLabel>
            <Select value={selectedPersonId} onChange={(e) => setSelectedPersonId(e.target.value)} label="Select Existing Person">
              {persons.map(p => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
            </Select>
          </FormControl>
          <Button fullWidth variant="contained" onClick={handleAssignFace} sx={{ mt: 2 }} disabled={!newPersonName && !selectedPersonId}>
            Assign
          </Button>
        </DialogContent>
      </Dialog>
    </Container>
  )
}
