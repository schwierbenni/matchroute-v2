import React, { useState, useEffect } from "react";
import axios from "axios";
import './RegisterForm.css';

const RegisterForm = () => {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
    lieblingsverein: "",
  });

  const [vereine, setVereine] = useState([]);
  const [message, setMessage] = useState(null);

  // Vereine beim Laden der Komponenten abrufen
  useEffect(() => {
    axios.get(`${process.env.REACT_APP_API_URL}/parkplatz/verein/`)
        .then((response) => setVereine(response.data))
        .catch((err) => console.error('Fehler beim Laden der Vereine:', err));
    }, []);

  // Formulareingabe verwalten
  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // Registrierung absenden
  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post(`${process.env.REACT_APP_API_URL}/parkplatz/register/`, form)
      .then((res) => {
        setMessage('Registrierung erfolgreich!');
        console.log('Erfolg:', res.data);
      })
      .catch((err) => {
        setMessage('Fehler bei der Registrierung');
        console.error('Fehler:', err.response?.data);
      });
  };
  
  return (
    <div className="register-container">
      <h2>Registrierung</h2>
      {message && <p className="message">{message}</p>}

      <form onSubmit={handleSubmit} className="register-form">
        <input type="text" name="username" placeholder="Benutzername" onChange={handleChange} required />
        <input type="email" name="email" placeholder="E-Mail" onChange={handleChange} required />
        <input type="password" name="password" placeholder="Passwort" onChange={handleChange} required />
        <input type="password" name="password2" placeholder="Passwort bestätigen" onChange={handleChange} required />

        <select name="lieblingsverein" onChange={handleChange} required>
          <option value="">Lieblingsverein wählen</option>
          {vereine.map(v => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>

        <button type="submit">Jetzt registrieren</button>
      </form>
    </div>
  );

};

export default RegisterForm;
