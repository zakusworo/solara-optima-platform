import { useEffect, useRef, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Create a simple circle marker instead of default icon (avores PNG import issues)
function createMarkerIcon() {
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      width: 20px; height: 20px; 
      background: #3A7010; border-radius: 50%;
      border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  })
}

interface LocationMapProps {
  latitude: number
  longitude: number
  onLocationChange: (lat: number, lon: number) => void
}

export default function LocationMap({ latitude, longitude, onLocationChange }: LocationMapProps) {
  const mapRef = useRef<L.Map | null>(null)
  const markerRef = useRef<L.Marker | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  const initMap = useCallback(() => {
    if (!containerRef.current || mapRef.current) return

    const map = L.map(containerRef.current).setView([latitude, longitude], 13)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map)

    const marker = L.marker([latitude, longitude], {
      icon: createMarkerIcon(),
      draggable: true,
    }).addTo(map)

    marker.on('dragend', (e) => {
      const latlng = (e.target as L.Marker).getLatLng()
      onLocationChange(latlng.lat, latlng.lng)
    })

    map.on('click', (e) => {
      marker.setLatLng(e.latlng)
      onLocationChange(e.latlng.lat, e.latlng.lng)
    })

    mapRef.current = map
    markerRef.current = marker
  }, [])

  useEffect(() => {
    initMap()
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
        markerRef.current = null
      }
    }
  }, [])

  // Update marker position when props change
  useEffect(() => {
    if (markerRef.current) {
      markerRef.current.setLatLng([latitude, longitude])
    }
    if (mapRef.current) {
      mapRef.current.setView([latitude, longitude])
    }
  }, [latitude, longitude])

  return (
    <div
      ref={containerRef}
      className="w-full h-full rounded-xl"
      style={{ minHeight: '300px' }}
    />
  )
}
