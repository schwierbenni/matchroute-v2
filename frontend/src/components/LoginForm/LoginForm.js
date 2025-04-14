import React, { useState } from 'react';
import { loginUser } from '../../api/auth';
import './LoginForm.css';
import { useNavigate } from 'react-router-dom';

const LoginForm = () => {
    const [form, setForm] = useState({ username: '', password: '' });
    const [message, setMessage] = useState(null);
    const navigate = useNavigate();
    const handleChange = (e) => {
      setForm({ ...form, [e.target.name]: e.target.value });
    };
  
    const handleSubmit = async (e) => {
      e.preventDefault();
    
      try {
        const res = await loginUser(form);
        console.log("Login erfolgreich:", res.data);
    
        localStorage.setItem("access_token", res.data.access);
        localStorage.setItem("refresh_token", res.data.refresh);
    
        setMessage("Login erfolgreich!");
        navigate("/dashboard");  // nach dem Speichern & Setzen
    
      } catch (error) {
        console.error("Fehler beim Login:", error?.response?.data || error);
        setMessage("Login fehlgeschlagen");
      }
    };

    return (
      <div className="login-container">
        <h2>Login</h2>
        {message && <p className="message">{message}</p>}
        <form onSubmit={handleSubmit} className="login-form">
          <input type="text" name="username" placeholder="Benutzername" onChange={handleChange} required />
          <input type="password" name="password" placeholder="Passwort" onChange={handleChange} required />
          <button type="submit">Login</button>
        </form>
      </div>
    );
  };
  
  export default LoginForm;