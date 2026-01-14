import { Container, Typography, Button, Box, Paper, Grid, Card, CardContent } from '@mui/material'
import { PhotoLibrary, Face, SmartToy, Search } from '@mui/icons-material'
import Link from 'next/link'

export default function Home() {
  const features = [
    {
      icon: <PhotoLibrary sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Upload Photos',
      description: 'Upload your photos and let AI detect all faces automatically'
    },
    {
      icon: <Face sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Name Faces',
      description: 'Add names to detected faces and system remembers them'
    },
    {
      icon: <SmartToy sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Auto Recognition',
      description: 'AI automatically identifies known people in new photos'
    },
    {
      icon: <Search sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Smart Search',
      description: 'Filter and find all photos containing specific people'
    }
  ]

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      py: 8
    }}>
      <Container maxWidth="lg">
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Typography 
            variant="h1" 
            component="h1" 
            sx={{ 
              color: 'white',
              mb: 3,
              fontWeight: 700,
              textShadow: '0 2px 4px rgba(0,0,0,0.3)'
            }}
          >
            SmartGallery
          </Typography>
          <Typography 
            variant="h5" 
            sx={{ 
              color: 'rgba(255,255,255,0.9)',
              mb: 6,
              maxWidth: 600,
              mx: 'auto'
            }}
          >
            AI-Powered Photo Gallery with Face Recognition
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button 
              variant="contained" 
              size="large"
              component={Link}
              href="/auth/register"
              sx={{ 
                bgcolor: 'white',
                color: 'primary.main',
                '&:hover': { bgcolor: 'grey.100' },
                px: 4,
                py: 1.5
              }}
            >
              Get Started
            </Button>
            <Button 
              variant="outlined" 
              size="large"
              component={Link}
              href="/auth/login"
              sx={{ 
                borderColor: 'white',
                color: 'white',
                '&:hover': { 
                  borderColor: 'white',
                  bgcolor: 'rgba(255,255,255,0.1)'
                },
                px: 4,
                py: 1.5
              }}
            >
              Login
            </Button>
          </Box>
        </Box>

        <Paper 
          elevation={0} 
          sx={{ 
            p: 6, 
            borderRadius: 4,
            bgcolor: 'rgba(255,255,255,0.95)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <Typography 
            variant="h4" 
            component="h2" 
            align="center" 
            sx={{ mb: 6, color: 'text.primary' }}
          >
            Features
          </Typography>
          
          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Card 
                  elevation={0}
                  sx={{ 
                    height: '100%',
                    textAlign: 'center',
                    border: '1px solid',
                    borderColor: 'grey.200',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 8px 25px rgba(0,0,0,0.1)'
                    }
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ mb: 2 }}>
                      {feature.icon}
                    </Box>
                    <Typography variant="h6" component="h3" sx={{ mb: 2 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Container>
    </Box>
  )
}