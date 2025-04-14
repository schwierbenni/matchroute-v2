import React, { useEffect, useState } from 'react';
import axiosClient from '../api/axiosClient';

const DashboardPage = () => {
  const [profil, setProfil] = useState(null);

  useEffect(() => {
    axiosClient.get('parkplatz/profil/')
      .then(res => {
        console.log('Profil geladen:', res.data);
        setProfil(res.data);
      })
      .catch(err => {
        console.error('Fehler beim Laden des Profils:', err);
      });
  }, []);

  if (!profil) {
    return <p>Lade dein Profil...</p>;
  }

  return (
    <div style={{ maxWidth: '600px', margin: 'auto', textAlign: 'center' }}>
      <h2>Willkommen, {profil.username}!</h2>
      <p><strong>E-Mail:</strong> {profil.email}</p>
      {profil.lieblingsverein ? (
        <p><strong>Lieblingsverein:</strong> {profil.lieblingsverein.name}</p>
      ) : (
        <p>Kein Lieblingsverein gesetzt.</p>
      )}
    </div>
  );
};

export default DashboardPage;