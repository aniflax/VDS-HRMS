const locationLabelCache = new Map();

export const getAttendanceCoordinateKey = (log) => {
  if (log?.location_lat === null || log?.location_lat === undefined || log?.location_lng === null || log?.location_lng === undefined) {
    return null;
  }
  const lat = Number(log.location_lat);
  const lng = Number(log.location_lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return null;
  }
  return `${lat.toFixed(6)},${lng.toFixed(6)}`;
};

const compactLocationLabel = (data) => {
  const address = data?.address || {};
  const exactName = data?.name
    || data?.namedetails?.name
    || address.amenity
    || address.building
    || address.office
    || address.shop
    || address.tourism
    || address.leisure;

  if (exactName) {
    return exactName;
  }

  const nearbyParts = [
    address.road || address.pedestrian || address.footway,
    address.neighbourhood || address.suburb || address.quarter || address.village || address.city_district,
    address.city || address.town || address.county,
  ].filter(Boolean);

  if (nearbyParts.length > 0) {
    return `near ${nearbyParts.slice(0, 3).join(', ')}`;
  }

  const displayParts = String(data?.display_name || '')
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean);

  return displayParts.length > 0 ? `near ${displayParts.slice(0, 3).join(', ')}` : null;
};

export const resolveAttendanceLocationLabel = async (lat, lng) => {
  const coordinateKey = `${Number(lat).toFixed(6)},${Number(lng).toFixed(6)}`;
  if (locationLabelCache.has(coordinateKey)) {
    return locationLabelCache.get(coordinateKey);
  }

  try {
    const params = new URLSearchParams({
      format: 'jsonv2',
      lat: String(lat),
      lon: String(lng),
      addressdetails: '1',
      namedetails: '1',
      zoom: '18',
      'accept-language': 'en',
    });
    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?${params.toString()}`);
    if (!response.ok) {
      throw new Error('Reverse geocoding failed');
    }
    const data = await response.json();
    const label = compactLocationLabel(data);
    locationLabelCache.set(coordinateKey, label);
    return label;
  } catch {
    locationLabelCache.set(coordinateKey, null);
    return null;
  }
};
