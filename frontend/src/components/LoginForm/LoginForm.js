import React, { useState } from 'react';
import { loginUser } from '../../api/auth';
import './LoginForm.css';

const LoginForm = () => {
    const [form, setForm] = useState({ username: '', password: '' });
    const [message, setMessage] = useState(null);
  
    const handleChange = (e) => {
      setForm({ ...form, [e.target.name]: e.target.value });
    };
  
    const handleSubmit = (e) => {
      e.preventDefault();
      loginUser(form)
        .then(res => {
          localStorage.setItem('access_token', res.data.access);
          localStorage.setItem('refresh_token', res.data.refresh);
          setMessage('Login erfolgreich!');
          console.log('Token gespeichert');
        })
        .catch(err => {
          setMessage('Login fehlgeschlagen');
          console.error(err.response?.data);
        });
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