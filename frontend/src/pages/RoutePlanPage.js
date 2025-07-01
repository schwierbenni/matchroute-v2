import React, { useState, useEffect } from "react";
import { 
  MapPin, 
  Navigation, 
  Clock, 
  Zap, 
  CheckCircle,
  Save,
  AlertTriangle
} from "lucide-react";
import axiosClient from "../api/axiosClient";
import {
  MapContainer,
  TileLayer,
  Polyline,
  Popup,
  useMap,
  CircleMarker,
} from "react-leaflet";
import { decodePolyline } from "../utils/decodePolyline";
import LoadingSpinner from "../components/LoadingSpinner/LoadingSpinner";
import ParkplatzCard from "../components/ParkplatzCard/ParkplatzCard";
import "leaflet/dist/leaflet.css";

const formatMinutes = (min) => {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h > 0 ? `${h}h ${m}min` : `${m}min`;
};

const getTrafficColorClass = (rating) => {
  if (rating >= 5) return 'from-green-500 to-emerald-500';
  if (rating >= 4) return 'from-blue-500 to-cyan-500';
  if (rating >= 3) return 'from-yellow-500 to-orange-400';
  if (rating >= 2) return 'from-orange-500 to-red-400';
  return 'from-red-600 to-red-700';
};

const getTrafficIcon = (rating) => {
  if (rating >= 4) return CheckCircle;
  if (rating >= 3) return Clock;
  return AlertTriangle;
};

const getTrafficDescription = (rating) => {
  const descriptions = {
    5: 'Excellent - Freie Fahrt',
    4: 'Good - Flüssiger Verkehr',
    3: 'Fair - Moderater Verkehr',
    2: 'Poor - Dichter Verkehr',
    1: 'Critical - Stau/Stockungen'
  };
  return descriptions[rating] || 'Unbekannt';
};

// Komponente für dynamisches Kartenzentrieren
const MapFocusController = ({ position, zoom = 15 }) => {
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

const RoutePlanPage = () => {
  const [startAdresse, setStartAdresse] = useState("");
  const [ergebnis, setErgebnis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("");
  const [routeCoords, setRouteCoords] = useState([]);
  const [transitCoords, setTransitCoords] = useState([]);
  const [startMarker, setStartMarker] = useState(null);
  const [zielMarker, setZielMarker] = useState(null);
  const [alleVorschlaege, setAlleVorschlaege] = useState([]);
  const [stadionId, setStadionId] = useState(null);
  const [fokusParkplatz, setFokusParkplatz] = useState(null);
  const [aktiverParkplatz, setAktiverParkplatz] = useState(null);
  const [stadion, setStadion] = useState(null);
  const [verein, setVerein] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [fehlerMeldung, setFehlerMeldung] = useState("");

  // URL-Parameter für vorausgefüllte Adresse
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const addressParam = urlParams.get('address');
    if (addressParam) {
      setStartAdresse(decodeURIComponent(addressParam));
    }
  }, []);

  useEffect(() => {
    const fetchProfil = async () => {
      try {
        const res = await axiosClient.get("api/profil/");
        const id = res.data?.stadion?.id;
        setStadion(res.data?.stadion);
        setVerein(res.data?.lieblingsverein);
        if (id) setStadionId(id);
      } catch (err) {
        console.error("Profil konnte nicht geladen werden:", err);
        setFehlerMeldung("Profil konnte nicht geladen werden. Bitte versuchen Sie es erneut.");
      }
    };
    fetchProfil();
  }, []);

  // Event Listener für Parkplatz-Fokus von den Karten
  useEffect(() => {
    const handleParkplatzFocus = (event) => {
      const { lat, lng } = event.detail;
      setFokusParkplatz([lat, lng]);
    };

    window.addEventListener('focusParkplatz', handleParkplatzFocus);
    
    return () => {
      window.removeEventListener('focusParkplatz', handleParkplatzFocus);
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setFehlerMeldung("");
    setLoadingStage("Adresse wird validiert...");
    resetRouteData();

    try {
      setLoadingStage("Verkehrsdaten werden analysiert...");
      
      const res = await axiosClient.post("api/routen-vorschlag/", {
        start_adresse: startAdresse,
      });

      setLoadingStage("Parkplatz-Optionen werden optimiert...");

      const sorted = [
        res.data?.empfohlener_parkplatz,
        ...(res.data?.alle_parkplaetze || []),
      ];
      
      setAlleVorschlaege(sorted);
      setErgebnis(res.data);

      const route = sorted[0];
      if (route?.polyline_auto) {
        const coords = decodePolyline(route.polyline_auto);
        setRouteCoords(coords);
        setStartMarker(coords[0]);
        setZielMarker(coords[coords.length - 1]);
      }
      
      if (route?.polyline_transit || route?.polyline_walking) {
        setTransitCoords(
          decodePolyline(route.polyline_transit || route.polyline_walking)
        );
      }
      
      // Fokus auf empfohlenen Parkplatz setzen
      setFokusParkplatz([route.parkplatz.latitude, route.parkplatz.longitude]);
      setAktiverParkplatz(route);

      setLoadingStage("Fertig!");
      
    } catch (err) {
      console.error("Fehler beim Berechnen der Route:", err);
      
      if (err.response?.status === 400) {
        setFehlerMeldung("Die eingegebene Adresse konnte nicht gefunden werden. Bitte überprüfen Sie Ihre Eingabe.");
      } else if (err.response?.status === 429) {
        setFehlerMeldung("Zu viele Anfragen. Bitte warten Sie einen Moment und versuchen Sie es erneut.");
      } else {
        setFehlerMeldung("Es ist ein Fehler bei der Routenberechnung aufgetreten. Bitte versuchen Sie es später erneut.");
      }
    }

    setIsLoading(false);
    setLoadingStage("");
  };

  const resetRouteData = () => {
    setErgebnis(null);
    setRouteCoords([]);
    setTransitCoords([]);
    setStartMarker(null);
    setZielMarker(null);
    setAlleVorschlaege([]);
    setAktiverParkplatz(null);
    setFehlerMeldung("");
  };

  const handleParkplatzKlick = (v) => {
    // Sofort Fokus setzen für bessere Responsivität
    setFokusParkplatz([v.parkplatz.latitude, v.parkplatz.longitude]);
    setAktiverParkplatz(v);
    
    // Route-Daten aktualisieren
    if (v?.polyline_auto) {
      const coords = decodePolyline(v.polyline_auto);
      setRouteCoords(coords);
      setStartMarker(coords[0]);
      setZielMarker(coords[coords.length - 1]);
    }
    
    const polylineAlt = v.polyline_transit || v.polyline_walking;
    setTransitCoords(polylineAlt ? decodePolyline(polylineAlt) : []);
  };

  const handleSaveRoute = async () => {
    const route = aktiverParkplatz;
    if (!route || !route.parkplatz || !stadionId) {
      alert("Fehlende Informationen zum Speichern.");
      return;
    }

    setIsSaving(true);
    
    try {
      await axiosClient.post("api/routen/speichern/", {
        start_adresse: startAdresse,
        start_lat: startMarker?.[0],
        start_lng: startMarker?.[1],
        distanz_km: route.distanz_km,
        dauer_min: route.gesamtzeit,
        transportmittel: route.beste_methode?.toLowerCase() || "auto",
        stadion_id: stadionId,
        parkplatz_id: route.parkplatz.id,
        route_url: null,
      });
      
      alert("Route erfolgreich gespeichert! Sie finden sie in Ihrem Dashboard.");
    } catch (err) {
      console.error("Fehler beim Speichern der Route:", err);
      alert("Die Route konnte nicht gespeichert werden. Bitte versuchen Sie es erneut.");
    }
    
    setIsSaving(false);
  };

  const mapCenter =
    routeCoords.length > 0
      ? routeCoords[Math.floor(routeCoords.length / 2)]
      : [53.5511, 9.9937];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        
        {/* Enhanced Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 bg-white/70 backdrop-blur-sm rounded-2xl px-6 py-4 shadow-lg border border-white/20 mb-4">
            <Navigation className="w-8 h-8 text-indigo-600" />
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                Intelligenter Routenplaner
              </h1>
              <p className="text-gray-600 mt-1">Powered by Google Maps & AI</p>
            </div>
          </div>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Finde den optimalen Parkplatz mit Echtzeitverkehr für{" "}
            <span className="font-semibold text-indigo-600">
              {verein?.name || "deinen Verein"}
            </span>
          </p>
        </div>

        {/* Enhanced Stadium Info Card */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden border border-white/20">
            <div className="md:flex">
              <div className="md:w-1/3 relative">
                <img
                  src={stadion?.bild_url || "/placeholder.svg"}
                  alt="Stadion"
                  className="w-full h-48 md:h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent md:bg-gradient-to-r"></div>
              </div>
              <div className="md:w-2/3 p-6 relative">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800">
                      {stadion?.name || "Stadionname"}
                    </h2>
                    <p className="text-gray-600 mt-1 flex items-center">
                      <MapPin className="w-4 h-4 mr-2" />
                      {stadion?.adresse || "Stadionadresse"}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-lg">
                      {verein?.liga || "Liga"}
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">Team:</span>
                    <span className="font-medium">{verein?.name || "—"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">Stadt:</span>
                    <span className="font-medium">{verein?.stadt || "—"}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {fehlerMeldung && (
          <div className="max-w-4xl mx-auto mb-6">
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 shadow-lg">
              <div className="flex items-center">
                <AlertTriangle className="w-6 h-6 text-red-600 mr-3" />
                <div>
                  <h3 className="text-red-800 font-semibold">Fehler bei der Routenberechnung</h3>
                  <p className="text-red-700 text-sm mt-1">{fehlerMeldung}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
          
          {/* Left Column - Controls */}
          <div className="space-y-6">
            
            {/* Enhanced Search Form */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-white/20">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                <MapPin className="w-5 h-5 mr-2" />
                Startadresse eingeben
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="z.B. Hamburg, Hauptbahnhof oder Ihre vollständige Adresse"
                    value={startAdresse}
                    onChange={(e) => setStartAdresse(e.target.value)}
                    required
                    disabled={isLoading}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 disabled:bg-gray-100 text-lg"
                  />
                  {isLoading && (
                    <div className="absolute right-3 top-3">
                      <div className="animate-spin h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
                    </div>
                  )}
                </div>
                
                <button
                  type="submit"
                  disabled={isLoading || !startAdresse.trim()}
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium py-4 px-6 rounded-xl transition-all duration-200 transform hover:scale-105 disabled:scale-100 shadow-xl text-lg"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin -ml-1 mr-3 h-6 w-6 border-2 border-white border-t-transparent rounded-full"></div>
                      Route wird berechnet...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center">
                      <Navigation className="w-5 h-5 mr-2" />
                      Beste Route finden
                    </span>
                  )}
                </button>
                
                {loadingStage && (
                  <div className="text-center">
                    <p className="text-sm text-indigo-600 font-medium mb-2">{loadingStage}</p>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-gradient-to-r from-indigo-600 to-purple-600 h-3 rounded-full transition-all duration-500" 
                        style={{
                          width: loadingStage.includes("Fertig") ? "100%" : 
                                 loadingStage.includes("optimiert") ? "80%" : 
                                 loadingStage.includes("analysiert") ? "60%" : "30%"
                        }}
                      ></div>
                    </div>
                  </div>
                )}
              </form>
            </div>

            {/* Enhanced Traffic Assessment */}
            {ergebnis?.empfohlener_parkplatz?.verkehr_bewertung && (
              <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-white/20">
                <h4 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
                  <Zap className="w-5 h-5 mr-2" />
                  Live-Verkehrslage
                </h4>
                <div className="flex items-center gap-4 mb-4">
                  <div className={`text-2xl font-bold px-6 py-3 rounded-2xl text-white shadow-lg bg-gradient-to-r ${getTrafficColorClass(ergebnis.empfohlener_parkplatz.verkehr_bewertung)}`}>
                    {React.createElement(getTrafficIcon(ergebnis.empfohlener_parkplatz.verkehr_bewertung), { className: "w-6 h-6 mr-2 inline" })}
                    {ergebnis.empfohlener_parkplatz.verkehr_bewertung}/5
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-800">
                      {getTrafficDescription(ergebnis.empfohlener_parkplatz.verkehr_bewertung)}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      Basierend auf Live-Verkehrsdaten
                    </p>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <p className="text-gray-700 font-medium flex items-start">
                    <Zap className="w-4 h-4 mr-2 mt-0.5 text-blue-600" />
                    {ergebnis.empfohlener_parkplatz.verkehr_kommentar}
                  </p>
                </div>
              </div>
            )}

            {/* Enhanced Actions */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-white/20">
              <h4 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
                <Save className="w-5 h-5 mr-2" />
                Aktionen
              </h4>
              <div className="space-y-3">
                <button
                  onClick={handleSaveRoute}
                  disabled={!aktiverParkplatz || isSaving}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium py-3 px-6 rounded-xl transition-all duration-200 transform hover:scale-105 disabled:scale-100 shadow-lg"
                >
                  {isSaving ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                      Wird gespeichert...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center">
                      <Save className="w-5 h-5 mr-2" />
                      Route speichern
                    </span>
                  )}
                </button>
                
                {aktiverParkplatz && (
                  <div className="text-center bg-indigo-50 rounded-xl p-3 border border-indigo-200">
                    <p className="text-sm text-indigo-700 flex items-center justify-center">
                      <CheckCircle className="w-4 h-4 mr-2" />
                      <span className="font-medium">Ausgewählt:</span> 
                      <span className="ml-1">{aktiverParkplatz.parkplatz.name}</span>
                    </p>
                    <p className="text-xs text-indigo-600 mt-1 flex items-center justify-center">
                      <Clock className="w-3 h-3 mr-1" />
                      Gesamtzeit: {formatMinutes(aktiverParkplatz.gesamtzeit)}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Map & Results */}
          <div className="space-y-6">
            
            {/* Enhanced Interactive Map */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden border border-white/20">
              <div className="p-4 bg-gray-50/80 border-b border-gray-200">
                <h3 className="text-lg font-bold text-gray-800 flex items-center">
                  <MapPin className="w-5 h-5 mr-2" />
                  Live-Kartenansicht
                  {routeCoords.length > 0 && (
                    <span className="ml-2 text-sm font-normal text-green-600 bg-green-100 px-2 py-1 rounded-full flex items-center">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Route aktiv
                    </span>
                  )}
                </h3>
              </div>
              <div className="relative">
                <MapContainer
                  center={fokusParkplatz || mapCenter}
                  zoom={13}
                  style={{ height: "450px", width: "100%" }}
                  className="z-0"
                >
                  <MapFocusController position={fokusParkplatz} />
                  <TileLayer
                    attribution="&copy; OpenStreetMap"
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {routeCoords.length > 0 && (
                    <Polyline 
                      positions={routeCoords} 
                      color="#4F46E5" 
                      weight={5} 
                      opacity={0.8}
                      pathOptions={{
                        lineCap: 'round',
                        lineJoin: 'round'
                      }}
                    />
                  )}
                  {transitCoords.length > 0 && (
                    <Polyline
                      positions={transitCoords}
                      color="#059669"
                      dashArray="8"
                      weight={4}
                      opacity={0.7}
                      pathOptions={{
                        lineCap: 'round',
                        lineJoin: 'round'
                      }}
                    />
                  )}
                  {startMarker && (
                    <CircleMarker
                      center={startMarker}
                      radius={10}
                      pathOptions={{ 
                        color: "#DC2626", 
                        fillColor: "#FCA5A5", 
                        fillOpacity: 0.8,
                        weight: 3
                      }}
                    >
                      <Popup>
                        <div className="text-center font-medium">
                          <MapPin className="w-4 h-4 inline mr-1" />
                          Startadresse<br/>
                          <span className="text-sm text-gray-600">{startAdresse}</span>
                        </div>
                      </Popup>
                    </CircleMarker>
                  )}
                  {zielMarker && (
                    <CircleMarker
                      center={zielMarker}
                      radius={10}
                      pathOptions={{ 
                        color: "#1F2937", 
                        fillColor: "#6B7280", 
                        fillOpacity: 0.8,
                        weight: 3
                      }}
                    >
                      <Popup>
                        <div className="text-center font-medium">
                          <MapPin className="w-4 h-4 inline mr-1" />
                          Ziel-Parkplatz<br/>
                          <span className="text-sm text-gray-600">
                            {aktiverParkplatz?.parkplatz.name}
                          </span>
                        </div>
                      </Popup>
                    </CircleMarker>
                  )}
                </MapContainer>
                
                {/* Enhanced Map Legend */}
                <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-xl p-4 shadow-lg z-10 border border-gray-200 max-w-48">
                  <h4 className="font-semibold text-sm mb-3 text-gray-800 flex items-center">
                    <MapPin className="w-4 h-4 mr-1" />
                    Legende
                  </h4>
                  <div className="space-y-2 text-xs">
                    {routeCoords.length > 0 && (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-1 bg-indigo-600 rounded"></div>
                        <span className="text-gray-700">Auto-Route</span>
                      </div>
                    )}
                    {transitCoords.length > 0 && (
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-4 h-1 bg-green-600 rounded" 
                          style={{
                            background: 'linear-gradient(to right, #059669 4px, transparent 4px)', 
                            backgroundSize: '8px 1px',
                            backgroundRepeat: 'repeat-x'
                          }}
                        ></div>
                        <span className="text-gray-700">Weiterreise</span>
                      </div>
                    )}
                    
                    <div className="border-t border-gray-200 pt-2 space-y-1">
                      {startMarker && (
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-red-300 border-2 border-red-600 rounded-full"></div>
                          <span className="text-gray-700">Start</span>
                        </div>
                      )}
                      {zielMarker && (
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-gray-400 border-2 border-gray-800 rounded-full"></div>
                          <span className="text-gray-700">Parkplatz</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Map Statistics */}
                {(routeCoords.length > 0 || transitCoords.length > 0) && (
                  <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-xl p-3 shadow-lg z-10 border border-gray-200">
                    <h4 className="font-semibold text-sm mb-2 text-gray-800 flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      Routeninfo
                    </h4>
                    <div className="space-y-1 text-xs text-gray-700">
                      {aktiverParkplatz && (
                        <>
                          <div className="flex justify-between">
                            <span>Distanz:</span>
                            <span className="font-medium">{aktiverParkplatz.distanz_km} km</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Gesamtzeit:</span>
                            <span className="font-medium">{formatMinutes(aktiverParkplatz.gesamtzeit)}</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Enhanced Parking Results */}
            {alleVorschlaege.length > 0 && (
              <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20">
                <div className="p-4 bg-gray-50/80 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center">
                      <MapPin className="w-5 h-5 mr-2" />
                      Parkplatz-Optionen
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-600 bg-white px-3 py-1 rounded-full border">
                        {alleVorschlaege.length} verfügbar
                      </span>
                      <span className="text-xs text-gray-500 bg-green-100 text-green-700 px-2 py-1 rounded-full flex items-center">
                        <Zap className="w-3 h-3 mr-1" />
                        Live-Daten
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
                  {alleVorschlaege
                    .sort((a, b) => a.gesamtzeit - b.gesamtzeit)
                    .map((vorschlag, index) => (
                      <ParkplatzCard
                        key={vorschlag.parkplatz.id}
                        vorschlag={vorschlag}
                        index={index}
                        isActive={aktiverParkplatz?.parkplatz.id === vorschlag.parkplatz.id}
                        onClick={handleParkplatzKlick}
                      />
                    ))}
                </div>
                
                {/* Summary Footer */}
                <div className="p-4 bg-gray-50/80 border-t border-gray-200">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 flex items-center">
                      <CheckCircle className="w-4 h-4 mr-1" />
                      Beste Option: <span className="font-medium ml-1">{alleVorschlaege[0]?.parkplatz.name}</span>
                    </span>
                    <span className="text-indigo-600 font-medium flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      {formatMinutes(alleVorschlaege[0]?.gesamtzeit)} Gesamtzeit
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {isLoading && alleVorschlaege.length === 0 && (
              <LoadingSpinner message={loadingStage} />
            )}

            {/* Empty State */}
            {!isLoading && alleVorschlaege.length === 0 && !fehlerMeldung && (
              <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-white/20 text-center">
                <MapPin className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-800 mb-2">Bereit für die Routenplanung</h3>
                <p className="text-gray-600 mb-4">
                  Geben Sie Ihre Startadresse ein, um die besten Parkplatz-Optionen zu finden.
                </p>
                <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-200">
                  <p className="text-sm text-indigo-700 flex items-center justify-center">
                    <Zap className="w-4 h-4 mr-2" />
                    <strong>Tipp:</strong> Je genauer Ihre Adresse, desto präziser die Routenberechnung.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoutePlanPage;