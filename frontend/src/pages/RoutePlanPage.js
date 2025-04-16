import React, { useState, useEffect } from "react";
import axiosClient from "../api/axiosClient";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Popup,
} from "react-leaflet";
import { decodePolyline } from "../utils/decodePolyline";
import "leaflet/dist/leaflet.css";

const useDummyData = false; // Umschalten für Testbetrieb

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
      if (useDummyData) {
        const dummyResponse = {
          empfohlener_parkplatz: {
            parkplatz: {
              id: 5,
              name: "Parkhaus Stadion Nord",
              lat: 53.5665,
              lon: 9.9845,
            },
            gesamtzeit: 22,
            distanz_km: 4.8,
            beste_methode: "Auto + Fußweg",
            polyline_auto: "o}ynHusxw@k@k@{@m@{@g@c@k@o@wA_@y@Y]YY[o@o@",
            polyline_transit: "mxykHqvww@dAp@b@p@Z^h@n@l@l@t@r@b@",
          },
          alle_parkplaetze: [
            {
              parkplatz: {
                id: 10,
                name: "P1 Messe",
                lat: 53.5642,
                lon: 9.9821,
              },
              gesamtzeit: 25,
              distanz_km: 5.1,
            },
            {
              parkplatz: {
                id: 12,
                name: "P2 Uni Hamburg",
                lat: 53.565,
                lon: 9.99,
              },
              gesamtzeit: 28,
              distanz_km: 5.4,
            },
          ],
        };

        setErgebnis(dummyResponse);
        setAlleVorschlaege(dummyResponse.alle_parkplaetze || []);

        const route = dummyResponse.empfohlener_parkplatz;
        if (route?.polyline_auto) {
          const coords = decodePolyline(route.polyline_auto);
          setRouteCoords(coords);
          setStartMarker(coords[0]);
          setZielMarker(coords[coords.length - 1]);
        }
        if (route?.polyline_transit) {
          const coordsTransit = decodePolyline(route.polyline_transit);
          setTransitCoords(coordsTransit);
        }
      } else {
        const res = await axiosClient.post("api/routen-vorschlag/", {
          start_adresse: startAdresse,
        });
        setErgebnis(res.data);
        setAlleVorschlaege(res.data?.alle_parkplaetze || []);

        const route = res.data?.empfohlener_parkplatz;
        if (route?.polyline_auto) {
          const coords = decodePolyline(route.polyline_auto);
          setRouteCoords(coords);
          setStartMarker(coords[0]);
          setZielMarker(coords[coords.length - 1]);
        }
        if (route?.polyline_transit) {
          const coordsTransit = decodePolyline(route.polyline_transit);
          setTransitCoords(coordsTransit);
        }
      }
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

    if (useDummyData) {
      alert("💡 Speichern ist im Dummy-Modus deaktiviert.");
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

      alert("✅ Route erfolgreich gespeichert.");
    } catch (err) {
      console.error("Fehler beim Speichern der Route:", err);
      alert("❌ Route konnte nicht gespeichert werden.");
    }
  };

  const mapCenter =
    routeCoords.length > 0
      ? routeCoords[Math.floor(routeCoords.length / 2)]
      : alleVorschlaege.length > 0
      ? [alleVorschlaege[0].parkplatz.lat, alleVorschlaege[0].parkplatz.lon]
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

      {ergebnis?.empfohlener_parkplatz && (
        <div
          style={{
            marginTop: 24,
            backgroundColor: "#f4f4f4",
            padding: 16,
            borderRadius: 8,
          }}
        >
          <h3>✅ Empfohlener Parkplatz:</h3>
          <p>
            <strong>{ergebnis.empfohlener_parkplatz.parkplatz.name}</strong>
          </p>
          <p>Dauer (gesamt): {ergebnis.empfohlener_parkplatz.gesamtzeit} min</p>
          <p>Distanz: {ergebnis.empfohlener_parkplatz.distanz_km} km</p>
          <p>Bester Modus: {ergebnis.empfohlener_parkplatz.beste_methode}</p>

          <button
            onClick={handleSaveRoute}
            style={{
              marginTop: 12,
              padding: "8px 16px",
              borderRadius: "8px",
              backgroundColor: "#4caf50",
              color: "white",
              border: "none",
              cursor: "pointer",
            }}
          >
            💾 Route speichern
          </button>
        </div>
      )}

      {ergebnis?.detail && (
        <p style={{ color: "crimson", marginTop: 20 }}>{ergebnis.detail}</p>
      )}

      {(routeCoords.length > 0 || alleVorschlaege.length > 0) && (
        <div style={{ marginTop: 30 }}>
          <MapContainer
            center={mapCenter}
            zoom={13}
            style={{ height: "400px", width: "100%", borderRadius: "8px" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {routeCoords.length > 0 && (
              <Polyline positions={routeCoords} color="blue" />
            )}
            {transitCoords.length > 0 && (
              <Polyline positions={transitCoords} color="green" dashArray="6" />
            )}
            {startMarker && (
              <Marker position={startMarker}>
                <Popup>Startadresse</Popup>
              </Marker>
            )}
            {zielMarker && (
              <Marker position={zielMarker}>
                <Popup>Empfohlener Parkplatz</Popup>
              </Marker>
            )}

            {alleVorschlaege.map((v, index) => (
              <Marker
                key={index}
                position={[v.parkplatz.latitude, v.parkplatz.longitude]}
              >
                <Popup>
                  🅿️ <strong>{v.parkplatz.name}</strong>
                  <br />
                  Zeit: {v.gesamtzeit} min
                  <br />
                  Distanz: {v.distanz_km} km
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          <div style={{ marginTop: 12 }}>
            <p>
              <span style={{ color: "blue" }}>▬</span> Auto-Route
            </p>
            <p>
              <span style={{ color: "green" }}>▬</span> Transit-/Fußweg
            </p>
          </div>

          {alleVorschlaege.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <h4>🅿️ Weitere Parkplätze (nach Zeit sortiert):</h4>
              {alleVorschlaege
                .sort((a, b) => a.gesamtzeit - b.gesamtzeit)
                .map((v, i) => (
                  <div key={i} style={{ padding: "4px 0" }}>
                    <strong>{v.parkplatz.name}</strong> – {v.gesamtzeit} min,{" "}
                    {v.distanz_km} km
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RoutePlanPage;
