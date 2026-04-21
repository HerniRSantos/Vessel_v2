import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const SHIP_PATHS = {
  cargo: 'M12 2 L20 10 L20 40 L4 40 L4 10 Z',
  tanker: 'M10 2 L21 12 L21 44 L3 44 L3 12 Z',
  fishing: 'M12 4 L18 10 L18 24 L6 24 L6 10 Z',
  military: 'M12 0 L20 12 L16 48 L8 48 L4 12 Z',
  tug: 'M8 4 L16 12 L16 28 L8 32 L0 28 L0 12 Z',
  passenger: 'M12 2 L22 12 L18 42 L6 42 L2 12 Z',
  pleasure: 'M12 4 L16 12 L12 28 L8 12 Z',
  default: 'M12 2 L22 34 L12 26 L2 34 Z'
};

function getVesselPath(type) {
  const t = (type || '').toLowerCase();
  if (t.includes('cargo')) return SHIP_PATHS.cargo;
  if (t.includes('tanker')) return SHIP_PATHS.tanker;
  if (t.includes('fish')) return SHIP_PATHS.fishing;
  if (t.includes('milit') || t.includes('law')) return SHIP_PATHS.military;
  if (t.includes('tug') || t.includes('tow')) return SHIP_PATHS.tug;
  if (t.includes('passeng')) return SHIP_PATHS.passenger;
  if (t.includes('recre') || t.includes('pleas') || t.includes('yacht')) return SHIP_PATHS.pleasure;
  return SHIP_PATHS.default;
}

function getMarkerColor(suspicious) {
  return suspicious ? '#ff3d5a' : '#00ff9d';
}

function createVesselIcon(type, suspicious, course = 0) {
  const color = getMarkerColor(suspicious);
  const svgPath = getVesselPath(type);
  
  return L.divIcon({
    className: 'vessel-div-icon',
    html: `
      <div style="transform: rotate(${course}deg); width: 24px; height: 48px;">
        <svg viewBox="0 0 24 48" width="24" height="48">
          <path d="${svgPath}" fill="${color}" stroke="rgba(255,255,255,0.3)" stroke-width="1.5" />
        </svg>
      </div>
    `,
    iconSize: [24, 48],
    iconAnchor: [12, 24]
  });
}

function MapUpdater({ vessels, onVesselClick }) {
  const map = useMap();
  const markersRef = useRef({});
  const polylinesRef = useRef({});

  useEffect(() => {
    const currentMmsi = new Set(vessels.map(v => v.mmsi));

    Object.entries(markersRef.current).forEach(([mmsi, marker]) => {
      if (!currentMmsi.has(parseInt(mmsi))) {
        map.removeLayer(marker);
        delete markersRef.current[mmsi];
      }
    });

    Object.entries(polylinesRef.current).forEach(([mmsi, polyline]) => {
      if (!currentMmsi.has(parseInt(mmsi))) {
        map.removeLayer(polyline);
        delete polylinesRef.current[mmsi];
      }
    });

    vessels.forEach(vessel => {
      const { mmsi, lat, lon, type, suspicious, course, name } = vessel;
      if (!lat || !lon) return;

      const key = mmsi.toString();
      const pos = [lat, lon];
      const icon = createVesselIcon(type, suspicious, course);

      if (markersRef.current[key]) {
        const marker = markersRef.current[key];
        marker.setLatLng(pos);
        marker.setIcon(icon);
        const tooltipContent = `
          <div class="font-semibold">${name || `MMSI: ${mmsi}`}</div>
          <div class="opacity-70">${type || 'Desconhecido'}</div>
          <div class="${suspicious ? 'text-red-400' : 'text-green-400'} font-semibold">
            ${suspicious ? '⚠ SUSPEITA' : '✓ SEM ALERTAS'}
          </div>
        `;
        marker.setTooltipContent(tooltipContent);
      } else {
        const marker = L.marker(pos, { icon }).addTo(map);
        const tooltipContent = `
          <div class="font-semibold">${name || `MMSI: ${mmsi}`}</div>
          <div class="opacity-70">${type || 'Desconhecido'}</div>
          <div class="${suspicious ? 'text-red-400' : 'text-green-400'} font-semibold">
            ${suspicious ? '⚠ SUSPEITA' : '✓ SEM ALERTAS'}
          </div>
        `;
        marker.bindTooltip(tooltipContent, {
          direction: 'top',
          offset: [0, -20],
          className: 'vessel-tooltip'
        });
        marker.on('click', () => onVesselClick(vessel));
        markersRef.current[key] = marker;
      }
    });

  }, [vessels, map, onVesselClick]);

  return null;
}

export default function VesselMap({ vessels, onVesselClick }) {
  const center = [36.5, -8.5];
  const zoom = 7;

  return (
    <MapContainer 
      center={center} 
      zoom={zoom} 
      className="w-full h-full"
      zoomControl={false}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        maxZoom={19}
      />
      <MapUpdater vessels={vessels} onVesselClick={onVesselClick} />
    </MapContainer>
  );
}