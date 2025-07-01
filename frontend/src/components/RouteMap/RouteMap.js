import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Popup, useMap, CircleMarker, Marker } from 'react-leaflet';
import L from 'leaflet';

// Custom icons
const createCustomIcon = (emoji, color = '#4F46E5') => {
  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        border: 3px solid white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      ">
        ${emoji}
      </div>
    `,
    className: 'custom-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
};

const FlyToLocation = ({ position, zoom = 15 }) => {
  const map = useMap();
  
  useEffect(() => {
    if (position && position.length === 2) {
      map.flyTo(position, zoom, {
        duration: 1.5,
        easeLinearity: 0.1
      });
    }
  }, [position, zoom, map]);
  
  return null;
};

const RouteMap = ({ 
  center = [53.5511, 9.9937], 
  zoom = 13,
  autoRoute = [],
  transitRoute = [],
  startPoint = null,
  parkingPoint = null,
  stadiumPoint = null,
  focusPosition = null,
  onMapClick = null,
  className = ""
}) => {
  
  // Bestimme Kartenzentrum basierend auf verfügbaren Daten
  const mapCenter = focusPosition || 
                   (autoRoute.length > 0 ? autoRoute[Math.floor(autoRoute.length / 2)] : null) ||
                   center;

  return (
    <div className={`relative w-full h-full ${className}`}>
      <MapContainer
        center={mapCenter}
        zoom={zoom}
        style={{ height: "100%", width: "100%" }}
        className="z-0 rounded-lg"
      >
        {/* Flyto-Funktion für dynamisches Zentrum */}
        <FlyToLocation position={focusPosition} />
        
        {/* Base Tile Layer */}
        <TileLayer
          attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Auto-Route (blau, durchgezogen) */}
        {autoRoute.length > 0 && (
          <Polyline
            positions={autoRoute}
            color="#4F46E5"
            weight={5}
            opacity={0.8}
            pathOptions={{
              lineCap: 'round',
              lineJoin: 'round'
            }}
          >
            <Popup>
              <div className="font-medium">
                🚗 Fahrt zum Parkplatz<br/>
                <span className="text-sm text-gray-600">
                  Blaue Linie zeigt Ihre Autoroute
                </span>
              </div>
            </Popup>
          </Polyline>
        )}

        {/* Transit/Walking Route (grün, gestrichelt) */}
        {transitRoute.length > 0 && (
          <Polyline
            positions={transitRoute}
            color="#059669"
            weight={4}
            opacity={0.7}
            dashArray="10, 5"
            pathOptions={{
              lineCap: 'round',
              lineJoin: 'round'
            }}
          >
            <Popup>
              <div className="font-medium">
                🚶‍♂️ Weiterreise zum Stadion<br/>
                <span className="text-sm text-gray-600">
                  Grüne gestrichelte Linie
                </span>
              </div>
            </Popup>
          </Polyline>
        )}

        {/* Start Point Marker */}
        {startPoint && (
          <Marker
            position={startPoint}
            icon={createCustomIcon('📍', '#DC2626')}
          >
            <Popup>
              <div className="text-center">
                <strong>🚀 Startpunkt</strong><br/>
                <span className="text-sm text-gray-600">Ihre eingegebene Adresse</span>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Parking Point Marker */}
        {parkingPoint && (
          <Marker
            position={parkingPoint}
            icon={createCustomIcon('🅿️', '#7C3AED')}
          >
            <Popup>
              <div className="text-center">
                <strong>🅿️ Parkplatz</strong><br/>
                <span className="text-sm text-gray-600">Empfohlener Parkplatz</span>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Stadium Point Marker */}
        {stadiumPoint && (
          <Marker
            position={stadiumPoint}
            icon={createCustomIcon('🏟️', '#059669')}
          >
            <Popup>
              <div className="text-center">
                <strong>🏟️ Stadion</strong><br/>
                <span className="text-sm text-gray-600">Ihr Ziel</span>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Map Controls Overlay */}
      <div className="absolute top-4 right-4 bg-white bg-opacity-95 backdrop-blur-sm rounded-lg p-3 shadow-lg z-10 border border-gray-200">
        <h4 className="font-semibold text-sm mb-2 text-gray-800 flex items-center">
          🗺️ Kartenlegende
        </h4>
        <div className="space-y-2 text-xs">
          {autoRoute.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-indigo-600 rounded"></div>
              <span className="text-gray-700">Auto-Route</span>
            </div>
          )}
          {transitRoute.length > 0 && (
            <div className="flex items-center gap-2">
              <div 
                className="w-4 h-1 bg-green-600 rounded" 
                style={{
                  background: 'linear-gradient(to right, #059669 3px, transparent 3px)', 
                  backgroundSize: '6px 1px',
                  backgroundRepeat: 'repeat-x'
                }}
              ></div>
              <span className="text-gray-700">Weiterreise</span>
            </div>
          )}
          
          <div className="border-t border-gray-200 pt-2 mt-2 space-y-1">
            {startPoint && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-400 border-2 border-red-600 rounded-full"></div>
                <span className="text-gray-700">Start</span>
              </div>
            )}
            {parkingPoint && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-400 border-2 border-purple-600 rounded-full"></div>
                <span className="text-gray-700">Parkplatz</span>
              </div>
            )}
            {stadiumPoint && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-400 border-2 border-green-600 rounded-full"></div>
                <span className="text-gray-700">Stadion</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Map Statistics Overlay (bottom-left) */}
      {(autoRoute.length > 0 || transitRoute.length > 0) && (
        <div className="absolute bottom-4 left-4 bg-white bg-opacity-95 backdrop-blur-sm rounded-lg p-3 shadow-lg z-10 border border-gray-200">
          <h4 className="font-semibold text-sm mb-2 text-gray-800 flex items-center">
            📊 Routeninfo
          </h4>
          <div className="space-y-1 text-xs text-gray-700">
            {autoRoute.length > 0 && (
              <div>
                <span className="text-indigo-600">●</span> Auto: ~{autoRoute.length} Punkte
              </div>
            )}
            {transitRoute.length > 0 && (
              <div>
                <span className="text-green-600">●</span> Weiterreise: ~{transitRoute.length} Punkte
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RouteMap;