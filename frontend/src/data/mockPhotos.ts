/**
 * High-quality photographic imagery for urban incidents (Screen 4)
 */

export const SAMPLE_INCIDENT_PHOTOS = {
  pothole: 'https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&w=600&q=80',
  traffic_density: 'https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=600&q=80',
  road_hazard: 'https://images.unsplash.com/photo-1541888946425-d0fbb186c5f3?auto=format&fit=crop&w=600&q=80',
  accident: 'https://images.unsplash.com/photo-1543332164-6e82f355badc?auto=format&fit=crop&w=600&q=80',
}

export function getIncidentPhoto(type: string): string {
  const t = type.toLowerCase()
  if (t.includes('pothole')) return SAMPLE_INCIDENT_PHOTOS.pothole
  if (t.includes('traffic')) return SAMPLE_INCIDENT_PHOTOS.traffic_density
  if (t.includes('accident')) return SAMPLE_INCIDENT_PHOTOS.accident
  return SAMPLE_INCIDENT_PHOTOS.road_hazard
}
