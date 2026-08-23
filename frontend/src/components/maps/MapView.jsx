import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl } from 'react-leaflet';
import L from 'leaflet';

// Leaflet default icon fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Center of Bhopal coordinates
const BHOPAL_CENTER = [23.2599, 77.4126];

export const MapView = ({
  center = BHOPAL_CENTER,
  zoom = 12,
  markers = [],
  height = '350px',
  onMarkerClick,
}) => {
  return (
    <div style={{ height }} className="w-full rounded-2xl overflow-hidden border border-gray-200 shadow-sm relative z-0">
      <MapContainer
        center={center}
        zoom={zoom}
        zoomControl={false}
        scrollWheelZoom={false}
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ZoomControl position="bottomright" />
        {markers.map((m, i) => (
          <Marker
            key={m.id || i}
            position={[m.lat || m.location?.lat || 23.2599, m.lng || m.location?.lng || 77.4126]}
            eventHandlers={{
              click: () => onMarkerClick && onMarkerClick(m),
            }}
          >
            <Popup>
              <div className="p-1 max-w-xs text-xs font-sans">
                <span className="font-bold text-gray-900 block">{m.title || m.label}</span>
                <span className="text-emerald-700 font-semibold block mt-0.5">{m.ward || m.location?.ward}</span>
                {m.status && (
                  <span className="inline-block mt-1 bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded font-bold">
                    {m.status}
                  </span>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};
