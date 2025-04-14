import React, { useEffect, useState } from 'react';
import axiosClient from '../api/axiosClient';
import LogoutButton from '../components/LogoutButton/LogoutButton';

const DashboardPage = () => {
  const [profil, setProfil] = useState(null);

  useEffect(() => {
    axiosClient.get('/api/profil/')
      .then(res => setProfil(res.data))
      .catch(err => console.error('Fehler beim Laden des Profils:', err));
  }, []);

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', textAlign: 'center' }}>
      <h1>🏟️ MatchRoute Dashboard</h1>

      {profil ? (
        <>
          <h2>Hallo {profil.username} 👋</h2>
          <p>Dein Lieblingsverein: <strong>{profil.lieblingsverein.name}</strong></p>
          <p>Bereit für deine nächste Route?</p>
          <button style={{
            padding: '10px 20px',
            borderRadius: '8px',
            fontSize: '16px',
            backgroundColor: '#3f51b5',
            color: 'white',
            border: 'none',
            cursor: 'pointer'
          }}>
            Neue Route starten
          </button>
        </>
      ) : (
        <p>Profil wird geladen...</p>
      )}

      <LogoutButton />
    </div>
  );
};

export default DashboardPage;