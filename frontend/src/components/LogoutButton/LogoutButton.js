import React from 'react';
import { useNavigate } from 'react-router-dom';
import { logoutUser } from '../../api/auth';

const LogoutButton = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    logoutUser();          // Tokens löschen
    navigate('/login');    // React-Router Redirect
  };

  return (
    <button
      onClick={handleLogout}
      style={{
        padding: '10px 16px',
        backgroundColor: '#e53935',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        marginTop: '20px'
      }}
    >
      Logout
    </button>
  );
};

export default LogoutButton;