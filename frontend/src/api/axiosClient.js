import axios from 'axios';

const axiosClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

axiosClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  });
  
  // Token Refresh
  axiosClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
  
      if (
        error.response?.status === 401 &&
        !originalRequest._retry &&
        localStorage.getItem('refresh_token')
      ) {
        originalRequest._retry = true;
        const refreshToken = localStorage.getItem('refresh_token');
  
        try {
          const response = await axios.post(
            `${process.env.REACT_APP_API_URL}/api/token/refresh/`,
            { refresh: refreshToken }
          );
  
          const newAccessToken = response.data.access;
          localStorage.setItem('access_token', newAccessToken);
  
          // neuen Token im Header setzen
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
  
          // wiederhole den ursprünglichen Request
          return axiosClient(originalRequest);
  
        } catch (refreshError) {
          console.error('Token Refresh fehlgeschlagen:', refreshError);
  
          // Tokens löschen und optional redirecten
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
  
          return Promise.reject(refreshError);
        }
      }
  
      return Promise.reject(error);
    }
  );
  
  export default axiosClient;