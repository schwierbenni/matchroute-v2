import axios from 'axios';

export const loginUser = (credentials) => {
  return axios.post(
    `${process.env.REACT_APP_API_URL}/api/token/`,
    credentials,
    {
      headers: { 'Content-Type': 'application/json' }
    }
  );
};

export const logoutUser = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };