import React, { useState, useEffect } from "react";
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
import "leaflet/dist/leaflet.css";

const markerColors = {
  start: "red",
  ziel: "black",
  bester: "green",
  vorschlag: "blue",
  route: "blue",
  transit: "green",
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
  const [anleitung, setAnleitung] = useState([]);
  const [zeigeAnleitung, setZeigeAnleitung] = useState(false);
  const [aktiverParkplatz, setAktiverParkplatz] = useState(null);
  const [stadion, setStadion] = useState(null);
  const [verein, setVerein] = useState(null);

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
      }
    };
    fetchProfil();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    resetRouteData();

    try {
      const res = await axiosClient.post("api/routen-vorschlag/", {
        start_adresse: startAdresse,
      });

      const sorted = [
        res.data?.empfohlener_parkplatz,
        ...(res.data?.alle_parkplaetze || []),
      ];
      setAlleVorschlaege(sorted);
      setErgebnis(res.data);

      const route = sorted[0];
      const coords = decodePolyline(route.polyline_auto);
      setRouteCoords(coords);
      setTransitCoords(
        decodePolyline(route.polyline_transit || route.polyline_walking)
      );
      setStartMarker(coords[0]);
      setZielMarker(coords[coords.length - 1]);
      setFokusParkplatz([route.parkplatz.latitude, route.parkplatz.longitude]);
      setAktiverParkplatz(route);
    } catch (err) {
      console.error("Fehler beim Berechnen der Route:", err);
      setErgebnis({
        detail: "Fehler bei der Berechnung der Route: " + err.message,
      });
    }

    setIsLoading(false);
  };

  const resetRouteData = () => {
    setErgebnis(null);
    setRouteCoords([]);
    setTransitCoords([]);
    setStartMarker(null);
    setZielMarker(null);
    setAnleitung([]);
    setZeigeAnleitung(false);
  };

  const handleParkplatzKlick = (v) => {
    setFokusParkplatz([v.parkplatz.latitude, v.parkplatz.longitude]);
    if (v?.polyline_auto) {
      const coords = decodePolyline(v.polyline_auto);
      setRouteCoords(coords);
      setStartMarker(coords[0]);
      setZielMarker(coords[coords.length - 1]);
    }
    const polylineAlt = v.polyline_transit || v.polyline_walking;
    setTransitCoords(polylineAlt ? decodePolyline(polylineAlt) : []);
    setAktiverParkplatz(v);
  };

  const handleSaveRoute = async () => {
    const route = aktiverParkplatz;
    if (!route || !route.parkplatz || !stadionId) {
      alert("Fehlende Informationen zum Speichern.");
      return;
    }

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
      alert("Route erfolgreich gespeichert.");
    } catch (err) {
      console.error("Fehler beim Speichern der Route:", err);
      alert("Route konnte nicht gespeichert werden.");
    }
  };

  const handleStartNavigation = async () => {
    if (!startMarker || !zielMarker) {
      alert("Start- und Zielposition fehlen.");
      return;
    }

    const start = `${startMarker[0]},${startMarker[1]}`;
    const ziel = `${zielMarker[0]},${zielMarker[1]}`;

    try {
      const res = await axiosClient.get("/api/navigation", {
        params: { start, ziel, profile: "foot" },
      });

      setAnleitung(res.data.instructions || []);
      setZeigeAnleitung(true);
    } catch (err) {
      console.error("Fehler bei der Navigation:", err);
      alert("Fehler beim Abrufen der Navigation.");
    }
  };

  const mapCenter =
    routeCoords.length > 0
      ? routeCoords[Math.floor(routeCoords.length / 2)]
      : [53.5511, 9.9937];

  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-center">Routenplaner</h1>
      <div>
        <h2 className="text-xl font-semibold mb-4 text-center">
          Herzlich Willkommen beim Routenplaner
        </h2>
        <h3 className="text-xl font-light mb-4 text-center">
          Gib einfach deine Startadresse ein und klicke auf den Button.
          Anschließend schlägt dir das System den bestmöglichen Parkplatz rund um       
            <strong> {verein?.stadt || "—"} </strong> vor.
        </h3>
      </div>
      <div className="bg-white border rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-bold">
              {stadion?.name || "Stadionname"}
            </h2>
            <p className="text-sm text-gray-500">
              {stadion?.adresse || "Stadionadresse"}
            </p>
          </div>
        </div>

        <div className="rounded overflow-hidden border mb-3">
          <img
            src={stadion?.bild_url || "/placeholder.svg"}
            alt="Stadion"
            className="w-full h-40 object-cover"
          />
        </div>

        <div className="text-sm space-y-1">
          <p>
            <strong>Team:</strong> {verein?.name || "—"}
          </p>
          <p>
            <strong>Stadt:</strong> {verein?.stadt || "—"}
          </p>
          <p>
            <strong>Liga:</strong> {verein?.liga || "—"}
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Linke Spalte – Eingabe & Buttons */}
        <div className="space-y-6">
          <div className="bg-white border rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Startadresse</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="text"
                placeholder="z. B. Hamburg, ABC-Straße"
                value={startAdresse}
                onChange={(e) => setStartAdresse(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md"
              >
                Route berechnen
              </button>
            </form>
          </div>

          <div className="bg-white border rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Aktionen</h2>
            <div className="space-y-3">
              <button
                onClick={handleSaveRoute}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md"
              >
                Route speichern
              </button>
              <button
                onClick={handleStartNavigation}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md"
              >
                Navigation starten
              </button>
            </div>
          </div>
        </div>

        {/* 🗺 Rechte Spalte – Karte & Legende */}
        <div className="space-y-6">
          <div className="rounded-lg overflow-hidden border shadow-sm">
            <MapContainer
              center={fokusParkplatz || mapCenter}
              zoom={13}
              style={{ height: "400px", width: "100%" }}
            >
              <FlyTo position={fokusParkplatz} />
              <TileLayer
                attribution="&copy; OpenStreetMap"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {routeCoords.length > 0 && (
                <Polyline positions={routeCoords} color="blue" />
              )}
              {transitCoords.length > 0 && (
                <Polyline
                  positions={transitCoords}
                  color="green"
                  dashArray="6"
                />
              )}
              {startMarker && (
                <CircleMarker
                  center={startMarker}
                  radius={8}
                  pathOptions={{ color: "red" }}
                >
                  <Popup>Startadresse</Popup>
                </CircleMarker>
              )}
              {zielMarker && (
                <CircleMarker
                  center={zielMarker}
                  radius={8}
                  pathOptions={{ color: "black" }}
                >
                  <Popup>Parkplatz</Popup>
                </CircleMarker>
              )}
            </MapContainer>
          </div>

          {alleVorschlaege.length > 0 && (
            <div className="bg-white border rounded-lg shadow-sm p-6 space-y-4">
              <h3 className="text-lg font-semibold mb-4">
                Parkplätze (nach Dauer sortiert)
              </h3>

              <div className="grid gap-4">
                {alleVorschlaege
                  .sort((a, b) => a.gesamtzeit - b.gesamtzeit)
                  .map((v, i) => (
                    <div
                      key={v.parkplatz.id}
                      onClick={() => handleParkplatzKlick(v)}
                      className={`cursor-pointer p-4 border rounded-md transition hover:shadow-md ${
                        i === 0 ? "bg-green-50 border-green-400" : "bg-gray-50"
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <div>
                          <h4 className="text-md font-semibold">
                            {v.parkplatz.name}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {formatMinutes(v.gesamtzeit)} · 📏{" "}
                            {formatKm(v.distanz_km)}
                          </p>
                        </div>
                        {i === 0 && (
                          <span className="text-xs px-2 py-1 bg-green-600 text-white rounded-full font-medium">
                            Empfohlen
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          <div className="bg-white border rounded-lg p-4 shadow-sm">
            <h3 className="font-medium text-lg mb-2">Legende</h3>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>
                <span className="text-blue-600 font-bold">▬</span> Auto-Route
              </li>
              <li>
                <span className="text-green-600 font-bold">▬</span>{" "}
                Transit-/Fußweg
              </li>
              <li>
                <span className="text-red-600 font-bold">⬤</span> Startadresse
              </li>
              <li>
                <span className="text-black font-bold">⬤</span> Ziel (Parkplatz)
              </li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  );
};

export default RoutePlanPage;
