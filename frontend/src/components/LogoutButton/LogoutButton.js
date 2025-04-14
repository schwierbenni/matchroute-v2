import React from 'react';
import { logoutUser } from '../../api/auth';

const LogoutButton = () => {
  return (
    <button onClick={logoutUser} style={{
      padding: '10px 16px',
      backgroundColor: '#e53935',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      margin: '20px auto',
      display: 'block'
    }}>
      Logout
    </button>
  );
};

export default LogoutButton;