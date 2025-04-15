import React, { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";

const DashboardPage = () => {
  const [profil, setProfil] = useState(null);

  useEffect(() => {
    axiosClient
      .get("parkplatz/profil/")
      .then((res) => {
        console.log("Profil geladen:", res.data);
        setProfil(res.data);
      })
      .catch((err) => {
        console.error("Fehler beim Laden des Profils:", err);
      });
  }, []);

  if (!profil) {
    return <p>Lade dein Profil...</p>;
  }

  return (
    <div
      style={{ maxWidth: "700px", margin: "40px auto", fontFamily: "Segoe UI" }}
    >
      <h1 style={{ textAlign: "center" }}>MatchRoute Dashboard</h1>

      <div style={{ marginBottom: "30px", textAlign: "center" }}>
        <h2>Willkommen, {profil.username}!</h2>
        <p>
          <strong>E-Mail:</strong> {profil.email}
        </p>

        {profil.lieblingsverein ? (
          <p>
            Dein Lieblingsverein: <strong>{profil.lieblingsverein.name}</strong>
            <br />
            Liga: {profil.lieblingsverein.liga}
          </p>
        ) : (
          <p>Kein Lieblingsverein hinterlegt.</p>
        )}
      </div>

      {profil.stadion && (
        <div
          style={{
            backgroundColor: "#f2f2f2",
            padding: "20px",
            borderRadius: "12px",
            textAlign: "center",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
        >
          <h3>Dein Heimstadion</h3>
          <p>
            <strong>{profil.stadion.name}</strong>
          </p>
          <p>{profil.stadion.adresse}</p>

          {profil.stadion.bild_url && (
            <img
              src={profil.stadion.bild_url}
              alt={profil.stadion.name}
              style={{
                width: "100%",
                maxHeight: "350px",
                objectFit: "cover",
                borderRadius: "10px",
                marginTop: "10px",
              }}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
