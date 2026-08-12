import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Grid, IconButton, Alert, Card, CardContent, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, CircularProgress, InputAdornment, Chip, Divider
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CloseIcon from '@mui/icons-material/Close';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Default location: The Art of Living International Center, Bengaluru
const DEFAULT_POSITION = [12.8269, 77.5099];

// Map controller to update view when position changes
function MapController({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);
  return null;
}

// Map click handler component
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng);
    },
  });
  return null;
}

// Search control component
function SearchControl({ onLocationFound }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const map = useMap();

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      if (data && data.length > 0) {
        const { lat, lon, display_name } = data[0];
        map.setView([lat, lon], 16);
        onLocationFound({ lat: parseFloat(lat), lng: parseFloat(lon), address: display_name });
      }
    } catch (err) {
      console.error('Search failed:', err);
    }
    setSearching(false);
  };

  return (
    <Box sx={{ position: 'absolute', top: 10, left: 50, zIndex: 1000, display: 'flex', gap: 1 }}>
      <TextField
        size="small"
        placeholder="Search location..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        sx={{ bgcolor: 'white', borderRadius: 1, width: 250 }}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton size="small" onClick={handleSearch} disabled={searching}>
                {searching ? <CircularProgress size={16} /> : <SearchIcon />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
    </Box>
  );
}

// Location marker component
function LocationMarker({ position, onClick }) {
  const map = useMap();
  
  useEffect(() => {
    if (position) {
      map.setView(position, map.getZoom());
    }
  }, [position, map]);

  return position ? (
    <Marker position={position} eventHandlers={{ click: onClick }}>
      <Popup>Selected location</Popup>
    </Marker>
  ) : null;
}

export default function Locations() {
  const { user } = useAuth();
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [locationDetails, setLocationDetails] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    latitude: '',
    longitude: '',
    geo_threshold_meters: 500
  });
  const [locationLoading, setLocationLoading] = useState(false);
  const [mapPosition, setMapPosition] = useState(DEFAULT_POSITION); // Art of Living International Center

  const isSuperAdmin = user?.role === 'SUPER_ADMIN';

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      const res = await api.get('/api/locations/');
      setLocations(res.data);
    } catch {
      setError('Failed to fetch locations');
    } finally {
      setLoading(false);
    }
  };

  const fetchLocationDetails = async (id) => {
    try {
      const res = await api.get(`/api/locations/${id}`);
      setLocationDetails(res.data);
    } catch {
      setError('Failed to fetch location details');
    }
  };

  // View location
  const openViewDialog = async (loc) => {
    setSelectedLocation(loc);
    setMapPosition([loc.latitude, loc.longitude]);
    await fetchLocationDetails(loc.id);
    setViewDialogOpen(true);
  };

  // Add new location
  const openAddDialog = () => {
    setSelectedLocation(null);
    setFormData({ name: '', address: '', latitude: '', longitude: '', geo_threshold_meters: 500 });
    setMapPosition(DEFAULT_POSITION); // Art of Living International Center
    setEditDialogOpen(true);
  };

  // Edit existing location
  const openEditDialog = async (loc) => {
    setSelectedLocation(loc);
    setFormData({
      name: loc.name,
      address: loc.address || '',
      latitude: loc.latitude,
      longitude: loc.longitude,
      geo_threshold_meters: loc.geo_threshold_meters || 500
    });
    setMapPosition([loc.latitude, loc.longitude]);
    setViewDialogOpen(false);
    setEditDialogOpen(true);
  };

  const handleMapClick = (latlng) => {
    setFormData(prev => ({ ...prev, latitude: latlng.lat, longitude: latlng.lng }));
    setMapPosition([latlng.lat, latlng.lng]);
    // Reverse geocode to get address
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latlng.lat}&lon=${latlng.lng}`)
      .then(res => res.json())
      .then(data => {
        if (data.display_name) {
          setFormData(prev => ({ ...prev, address: data.display_name }));
        }
      })
      .catch(() => {});
  };

  const handleSearchResult = (result) => {
    setFormData(prev => ({ ...prev, latitude: result.lat, longitude: result.lng, address: result.address || prev.address }));
    setMapPosition([result.lat, result.lng]);
  };

  const getCurrentLocation = () => {
    setLocationLoading(true);
    if (!navigator.geolocation) {
      setLocationLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setFormData(prev => ({ ...prev, latitude, longitude }));
        setMapPosition([latitude, longitude]);
        setLocationLoading(false);
        // Reverse geocode
        fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
          .then(res => res.json())
          .then(data => {
            if (data.display_name) {
              setFormData(prev => ({ ...prev, address: data.display_name }));
            }
          })
          .catch(() => {});
      },
      () => setLocationLoading(false),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleSave = async () => {
    try {
      const payload = {
        name: formData.name,
        address: formData.address || null,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        geo_threshold_meters: parseInt(formData.geo_threshold_meters) || 500
      };

      if (selectedLocation) {
        await api.put(`/api/locations/${selectedLocation.id}`, payload);
        setSuccess('Location updated');
      } else {
        await api.post('/api/locations/', payload);
        setSuccess('Location created');
      }
      setEditDialogOpen(false);
      fetchLocations();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save location');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this location?')) return;
    try {
      await api.delete(`/api/locations/${id}`);
      setSuccess('Location deleted');
      setViewDialogOpen(false);
      fetchLocations();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete');
    }
  };

  if (!isSuperAdmin) {
    return (
      <Box p={4}>
        <Typography variant="h5" fontWeight="bold">Access Denied</Typography>
        <Typography color="text.secondary">Only Super Admin can manage locations.</Typography>
      </Box>
    );
  }

  if (loading) return <CircularProgress />;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">Location Management</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openAddDialog}>Add Location</Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Location Cards - Consistent sizing */}
      <Grid container spacing={3}>
        {locations.map((loc) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={loc.id}>
            <Card 
              variant="outlined" 
              sx={{ 
                cursor: 'pointer', 
                '&:hover': { boxShadow: 3, borderColor: 'primary.main' },
                transition: 'all 0.2s',
                height: '100%',
                display: 'flex',
                flexDirection: 'column'
              }} 
              onClick={() => openViewDialog(loc)}
            >
              <CardContent sx={{ p: 2, flex: 1, display: 'flex', flexDirection: 'column' }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <LocationOnIcon color="primary" />
                  <Typography variant="subtitle1" fontWeight="bold" noWrap>{loc.name}</Typography>
                </Box>
                <Box sx={{ width: '100%', height: 180, borderRadius: 1, overflow: 'hidden', flex: 1 }}>
                  <MapContainer
                    center={[loc.latitude, loc.longitude]}
                    zoom={16}
                    style={{ width: '100%', height: '100%' }}
                    dragging={false}
                    zoomControl={false}
                    scrollWheelZoom={false}
                    doubleClickZoom={false}
                    touchZoom={false}
                    attributionControl={false}
                  >
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    <Marker position={[loc.latitude, loc.longitude]} />
                  </MapContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {locations.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">No locations added yet. Click "Add Location" to create one.</Typography>
        </Paper>
      )}

      {/* View Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center" gap={1}>
              <LocationOnIcon color="primary" />
              <Typography variant="h5" fontWeight="bold">{selectedLocation?.name}</Typography>
            </Box>
            <Box>
              <IconButton onClick={() => openEditDialog(selectedLocation)}><EditIcon /></IconButton>
              <IconButton onClick={() => handleDelete(selectedLocation?.id)} color="error"><DeleteIcon /></IconButton>
              <IconButton onClick={() => setViewDialogOpen(false)}><CloseIcon /></IconButton>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {locationDetails && (
            <>
              {locationDetails.address && (
                <Typography color="text.secondary" mb={2}>{locationDetails.address}</Typography>
              )}
              
              <Typography variant="subtitle2" color="text.secondary">Geo Threshold: {locationDetails.geo_threshold_meters}m</Typography>
              
              <Box sx={{ width: '100%', height: 300, borderRadius: 1, overflow: 'hidden', my: 2 }}>
                <MapContainer
                  center={[locationDetails.latitude, locationDetails.longitude]}
                  zoom={16}
                  style={{ width: '100%', height: '100%' }}
                >
                  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                  <Marker position={[locationDetails.latitude, locationDetails.longitude]} />
                </MapContainer>
              </Box>

              <Divider sx={{ my: 2 }} />
              
              <Typography variant="h6" mb={2}>Departments Using This Location</Typography>
              {locationDetails.departments?.length > 0 ? (
                <Box display="flex" gap={1} flexWrap="wrap">
                  {locationDetails.departments.map(dept => (
                    <Chip
                      key={dept.id}
                      label={dept.name}
                      color={dept.is_primary ? "primary" : "default"}
                      variant={dept.is_primary ? "filled" : "outlined"}
                    />
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">No departments assigned to this location.</Typography>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit/Add Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedLocation ? 'Edit Location' : 'Add New Location'}</DialogTitle>
        <DialogContent>
          <Box pt={2} display="flex" flexDirection="column" gap={2}>
            <TextField label="Location Name" fullWidth required value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="e.g., Main Ashram" />
            <TextField label="Address" fullWidth multiline rows={2} value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              helperText="Auto-filled when you click on map" />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField label="Latitude" fullWidth required type="number" value={formData.latitude}
                  onChange={(e) => setFormData({ ...formData, latitude: e.target.value })} />
              </Grid>
              <Grid item xs={6}>
                <TextField label="Longitude" fullWidth required type="number" value={formData.longitude}
                  onChange={(e) => setFormData({ ...formData, longitude: e.target.value })} />
              </Grid>
            </Grid>
            <TextField label="Geo Threshold (meters)" fullWidth type="number" value={formData.geo_threshold_meters}
              onChange={(e) => setFormData({ ...formData, geo_threshold_meters: e.target.value })}
              helperText="Maximum allowed distance for attendance marking" />
            
            <Button variant="outlined" startIcon={locationLoading ? <CircularProgress size={18} /> : <MyLocationIcon />}
              onClick={getCurrentLocation} disabled={locationLoading}>
              {locationLoading ? 'Getting Location...' : 'Use My Current Location'}
            </Button>

            <Typography variant="subtitle2" fontWeight="bold">Click on Map to Select Location</Typography>
            <Box sx={{ width: '100%', height: 400, borderRadius: 1, overflow: 'hidden', position: 'relative', border: '1px solid #ddd' }}>
              <MapContainer
                center={mapPosition}
                zoom={15}
                style={{ width: '100%', height: '100%' }}
              >
                <TileLayer 
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                <MapController center={mapPosition} />
                <SearchControl onLocationFound={handleSearchResult} />
                <MapClickHandler onMapClick={handleMapClick} />
                {formData.latitude && formData.longitude && (
                  <Marker position={[parseFloat(formData.latitude), parseFloat(formData.longitude)]} />
                )}
              </MapContainer>
              {/* Current Location Button overlay */}
              <Button
                variant="outlined"
                size="small"
                onClick={getCurrentLocation}
                disabled={locationLoading}
                sx={{
                  position: 'absolute',
                  top: 16,
                  right: 16,
                  zIndex: 1200,
                  bgcolor: 'white',
                  color: 'primary.main',
                  border: '1px solid',
                  borderColor: 'primary.light',
                  fontWeight: 800,
                  '& .MuiButton-startIcon': { color: 'primary.main' },
                  '&:hover': {
                    bgcolor: '#fff7ef',
                    borderColor: 'primary.main',
                  },
                  boxShadow: 2
                }}
                startIcon={locationLoading ? <CircularProgress size={16} /> : <MyLocationIcon />}
              >
                {locationLoading ? 'Locating...' : 'My Location'}
              </Button>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={!formData.name || !formData.latitude || !formData.longitude}>
            {selectedLocation ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
