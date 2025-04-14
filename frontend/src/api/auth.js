import axiosClient from './axiosClient';

// Request, um Bearer Token zu erhalten 
export const loginUser = (credentials) => {
  return axiosClient.post('/api/token/', credentials);
};

export const logoutUser = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login'; // oder '/login' mit Router
  };