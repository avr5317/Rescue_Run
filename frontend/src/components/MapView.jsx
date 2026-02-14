import { useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, useMap, useMapEvents, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import LastUpdated from './LastUpdated';
import { STATUS_LABELS } from '../utils/requestProgress';

function ZoomControl() {
  const map = useMap();
  useEffect(() => {
    const zoom = L.control.zoom({ position: 'bottomright' });
    zoom.addTo(map);
    return () => zoom.remove();
  }, [map]);
  return null;
}

const CATEGORY_COLORS = {
  meds: '#dc2626',
  groceries: '#16a34a',
  shelter: '#2563eb',
  transport: '#9333ea',
  other: '#6b7280',
};

function categoryIcon(category) {
  const color = CATEGORY_COLORS[category] || CATEGORY_COLORS.other;
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: 28px; height: 28px;
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function MapBounds({ onBoundsChange }) {
  const map = useMap();
  const lastBoundsRef = useRef(null);

  useEffect(() => {
    const handler = () => {
      const b = map.getBounds();
      const key = `${b.getSouth()},${b.getWest()},${b.getNorth()},${b.getEast()}`;
      if (lastBoundsRef.current !== key) {
        lastBoundsRef.current = key;
        const bbox = `${b.getSouth()},${b.getWest()},${b.getNorth()},${b.getEast()}`;
        onBoundsChange(bbox);
      }
    };
    handler();
    map.on('moveend', handler);
    return () => map.off('moveend', handler);
  }, [map, onBoundsChange]);

  return null;
}

function Markers({ requests, onMarkerClick }) {
  return (
    <>
      {requests.map((r) => (
        <Marker
          key={r.id}
          position={[r.lat, r.lng]}
          icon={categoryIcon(r.category)}
          eventHandlers={{
            click: () => onMarkerClick(r),
          }}
        >
          <Popup>
            <span className="font-medium capitalize">{r.category}</span>
            <br />
            <span>{STATUS_LABELS[r.status] || r.status}</span>
            <br />
            <LastUpdated value={r.updated_at || r.created_at} className="!text-gray-600" />
            <br />
            <span className="text-sm text-gray-600">
              ${r.funded_amount?.toFixed(0) ?? 0} / ${r.funding_goal?.toFixed(0) ?? 0}
            </span>
          </Popup>
        </Marker>
      ))}
    </>
  );
}

function MapPicker({ pickedLocation, onMapPick }) {
  useMapEvents({
    click(e) {
      onMapPick?.({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });

  if (!pickedLocation) return null;

  return (
    <Marker position={[pickedLocation.lat, pickedLocation.lng]}>
      <Popup>Selected request location</Popup>
    </Marker>
  );
}

export default function MapView({
  requests = [],
  onBoundsChange,
  onRequestClick,
  pickedLocation,
  onMapPick,
  selectedRequestId,
}) {
  const onBoundsChangeCb = useCallback(
    (bbox) => onBoundsChange?.(bbox),
    [onBoundsChange]
  );
  const markerRequests = requests.filter(
    (r) =>
      r.status === 'open' ||
      r.status === 'funded' ||
      (['claimed', 'on_the_way', 'delivered'].includes(r.status) && r.id === selectedRequestId)
  );

  return (
    <div className="absolute inset-0 z-0">
      <MapContainer
        center={[42.3601, -71.0589]}
        zoom={13}
        className="h-full w-full"
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <MapBounds onBoundsChange={onBoundsChangeCb} />
        <MapPicker pickedLocation={pickedLocation} onMapPick={onMapPick} />
        <Markers requests={markerRequests} onMarkerClick={onRequestClick} />
        <ZoomControl />
      </MapContainer>
      <div className="leaflet-bottom leaflet-right absolute bottom-24 right-4 z-[1000]" />
    </div>
  );
}

export { CATEGORY_COLORS };
