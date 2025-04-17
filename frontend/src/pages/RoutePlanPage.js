import React, { useState, useEffect } from "react";
import axiosClient from "../api/axiosClient";
import {
  MapContainer,
  TileLayer,
  Polyline,
  Popup,
  useMap,
} from "react-leaflet";
import { decodePolyline } from "../utils/decodePolyline";
import "leaflet/dist/leaflet.css";
import { CircleMarker } from "react-leaflet";

const markerColors = {
  start: "red",
  ziel: "black",
  bester: "green",
  vorschlag: "blue",
  route: "blue",
  transit: "green"
};

const formatMinutes = (min) => {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h > 0 ? `${h}h ${m}min` : `${m}min`;
};

const formatKm = (km) => {
  return `${parseFloat(km).toFixed(1)} km`;
};

const FlyTo = ({ position }) => {
  const map = useMap();
  useEffect(() => {
    if (position) map.flyTo(position, 15);
  }, [position, map]);
  return null;
};

const RoutePlanPage = () => {
  const [startAdresse, setStartAdresse] = useState("");
  const [ergebnis, setErgebnis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [routeCoords, setRouteCoords] = useState([]);
  const [transitCoords, setTransitCoords] = useState([]);
  const [startMarker, setStartMarker] = useState(null);
  const [zielMarker, setZielMarker] = useState(null);
  const [alleVorschlaege, setAlleVorschlaege] = useState([]);
  const [stadionId, setStadionId] = useState(null);
  const [fokusParkplatz, setFokusParkplatz] = useState(null);

  useEffect(() => {
    const fetchProfil = async () => {
      try {
        const res = await axiosClient.get("api/profil/");
        const id = res.data?.stadion?.id;
        if (id) setStadionId(id);
      } catch (err) {
        console.error("Profil konnte nicht geladen werden:", err);
      }
    };
    fetchProfil();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErgebnis(null);
    setRouteCoords([]);
    setTransitCoords([]);
    setStartMarker(null);
    setZielMarker(null);

    try {
      const res = await axiosClient.post("api/routen-vorschlag/", {
        start_adresse: startAdresse,
      });
      setErgebnis(res.data);

      const sorted = [
        res.data?.empfohlener_parkplatz,
        ...(res.data?.alle_parkplaetze || []),
      ];
      setAlleVorschlaege(sorted);

      const route = sorted[0];
      const start = decodePolyline(route.polyline_auto);
      setRouteCoords(start);
      setTransitCoords(decodePolyline(route.polyline_transit || route.polyline_walking));
      setStartMarker(start[0]);
      setZielMarker(start[start.length - 1]);
      setFokusParkplatz([
        route.parkplatz.latitude,
        route.parkplatz.longitude,
      ]);
    } catch (err) {
      console.error("Fehler beim Berechnen der Route:", err);
      setErgebnis({
        detail: "Fehler bei der Berechnung der Route: " + err.message,
      });
    }

    setIsLoading(false);
  };

  const handleSaveRoute = async () => {
    const route = ergebnis?.empfohlener_parkplatz;
    if (!route || !route.parkplatz || !stadionId) {
      alert("Fehlende Informationen zum Speichern.");
      return;
    }

    try {
      await axiosClient.post("api/route/speichern/", {
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

      alert("Route erfolgreich gespeichert.");
    } catch (err) {
      console.error("Fehler beim Speichern der Route:", err);
      alert("Route konnte nicht gespeichert werden.");
    }
  };

  const handleParkplatzKlick = (v) => {
    setFokusParkplatz([v.parkplatz.latitude, v.parkplatz.longitude]);
    if (v?.polyline_auto) {
      const coords = decodePolyline(v.polyline_auto);
      setRouteCoords(coords);
      setStartMarker(coords[0]);
      setZielMarker(coords[coords.length - 1]);
    }
    const polylineAlt =
      v.polyline_transit || v.polyline_walking || null;
    if (polylineAlt) {
      setTransitCoords(decodePolyline(polylineAlt));
    } else {
      setTransitCoords([]);
    }
  };

  const mapCenter =
    routeCoords.length > 0
      ? routeCoords[Math.floor(routeCoords.length / 2)]
      : alleVorschlaege.length > 0
      ? [
          alleVorschlaege[0].parkplatz.latitude,
          alleVorschlaege[0].parkplatz.longitude,
        ]
      : [53.5511, 9.9937];

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "Segoe UI" }}>
      <h2>🧭 Route planen</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Startadresse (z. B. Hamburg, ABC-Straße)"
          value={startAdresse}
          onChange={(e) => setStartAdresse(e.target.value)}
          required
          style={{
            padding: "10px",
            width: "100%",
            marginBottom: "12px",
            borderRadius: "8px",
            border: "1px solid #ccc",
          }}
        />
        <button
          type="submit"
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            backgroundColor: "#3f51b5",
            color: "white",
            border: "none",
            cursor: "pointer",
          }}
        >
          ➕ Route berechnen
        </button>
      </form>

      {isLoading && <p style={{ marginTop: 16 }}>⏳ Route wird berechnet...</p>}

      {alleVorschlaege.length > 0 && (
        <>
          <MapContainer
            center={fokusParkplatz || mapCenter}
            zoom={13}
            style={{
              height: "700px",
              width: "100%",
              marginTop: 20,
              borderRadius: 8,
            }}
          >
            <FlyTo position={fokusParkplatz} />
            <TileLayer
              attribution="&copy; OpenStreetMap"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {routeCoords.length > 0 && (
              <Polyline positions={routeCoords} color={markerColors.route} />
            )}
            {transitCoords.length > 0 && (
              <Polyline
                positions={transitCoords}
                color={markerColors.transit}
                dashArray="6"
              />
            )}

            {startMarker && (
              <CircleMarker
                center={startMarker}
                radius={8}
                pathOptions={{ color: markerColors.start, fillOpacity: 0.6 }}
              >
                <Popup>Startadresse</Popup>
              </CircleMarker>
            )}

            {zielMarker && (
              <CircleMarker
                center={zielMarker}
                radius={8}
                pathOptions={{ color: markerColors.ziel, fillOpacity: 0.6 }}
              >
                <Popup>Empfohlener Parkplatz</Popup>
              </CircleMarker>
            )}

            {alleVorschlaege.map((v, i) => (
              <CircleMarker
                key={v.parkplatz.id}
                center={[v.parkplatz.latitude, v.parkplatz.longitude]}
                radius={8}
                pathOptions={{
                  color: i === 0 ? markerColors.bester : markerColors.vorschlag,
                  fillOpacity: 0.6,
                }}
              >
                <Popup>
                  <strong>{v.parkplatz.name}</strong>
                  <br />
                  {formatMinutes(v.gesamtzeit)}
                  <br />
                  {formatKm(v.distanz_km)}
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>

          <div style={{ marginTop: 16 }}>
            <h4>Parkplätze (sortiert nach Dauer)</h4>
            {alleVorschlaege.map((v, i) => (
              <div
                key={v.parkplatz.id}
                onClick={() => handleParkplatzKlick(v)}
                style={{
                  padding: "10px",
                  marginBottom: "10px",
                  border: "1px solid #ccc",
                  borderRadius: 6,
                  backgroundColor: i === 0 ? "#e8f5e9" : "#f9f9f9",
                  cursor: "pointer",
                  boxShadow: i === 0 ? "0 0 6px rgba(0, 128, 0, 0.3)" : "none",
                }}
              >
                <p style={{ margin: 0, fontWeight: 600 }}>{v.parkplatz.name}</p>
                <p style={{ margin: 0 }}>
                  {formatMinutes(v.gesamtzeit)} · 📏 {formatKm(v.distanz_km)}
                </p>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 10, fontSize: "14px", color: "#555" }}>
            <strong>Legende:</strong>
            <br />
            <span style={{ color: markerColors.start }}>⬤</span> Startadresse
            <br />
            <span style={{ color: markerColors.ziel }}>⬤</span> Ziel
            (empfohlener Parkplatz)
            <br />
            <span style={{ color: markerColors.bester }}>⬤</span> Bester
            Vorschlag
            <br />
            <span style={{ color: markerColors.vorschlag }}>⬤</span> Weitere
            Parkplätze
            <br />
            <span style={{ color: markerColors.route }}>▬</span> Auto-Route
            <br />
            <span style={{ color: markerColors.transit }}>▬</span> Transit-/Fußweg
          </div>
        </>
      )}
    </div>
  );
};

export default RoutePlanPage;
