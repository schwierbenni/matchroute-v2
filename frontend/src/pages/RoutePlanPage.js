import React from "react";
import { useState } from "react";
import axiosClient from "../api/axiosClient";

const RoutePlanPage = () => {
    const [startAdresse, setStartAdresse] = useState("");
    const [ergebnis, setErgebnis] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setErgebnis(null); 

        try {
            const res = await axiosClient.post('parkplatz/routen-vorschlag/', {
                start_adresse: startAdresse,
            });
            setErgebnis(res.data);
        } catch (err) {
            console.error("Fehler beim Berechnen der Route:", err);
            setErgebnis({"Fehler bei der Berechnung der Route": err.message});
        }
        setIsLoading(false);
    }


    return (
        <div style={{ maxWidth: 600, margin: 'auto', paddingTop: 40 }}>
          <h2>Route planen</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Startadresse (z. B. Hamburg, ABC-Straße)"
              value={startAdresse}
              onChange={(e) => setStartAdresse(e.target.value)}
              style={{
                padding: '10px',
                width: '100%',
                marginBottom: '12px',
                borderRadius: '8px',
                border: '1px solid #ccc'
              }}
              required
            />
            <button
              type="submit"
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                backgroundColor: '#3f51b5',
                color: 'white',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              Route berechnen
            </button>
          </form>
    
          {isLoading && <p>Route wird berechnet...</p>}
    
          {ergebnis && ergebnis.empfohlener_parkplatz && (
            <div style={{ marginTop: 24, backgroundColor: '#f4f4f4', padding: 16, borderRadius: 8 }}>
              <h3>Empfohlener Parkplatz:</h3>
              <p><strong>{ergebnis.empfohlener_parkplatz.parkplatz.name}</strong></p>
              <p>Dauer (gesamt): {ergebnis.empfohlener_parkplatz.gesamtzeit} min</p>
              <p>Distanz: {ergebnis.empfohlener_parkplatz.distanz_km} km</p>
              <p>Bester Modus: {ergebnis.empfohlener_parkplatz.beste_methode}</p>
            </div>
          )}
    
          {ergebnis && ergebnis.detail && (
            <p style={{ color: 'crimson', marginTop: 20 }}>{ergebnis.detail}</p>
          )}
        </div>
      );
};

export default RoutePlanPage;
