import axios from 'axios';

// Base configuration
const axiosClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/',
  timeout: 30000, // Erhöht für komplexe Routenberechnungen
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor - Add auth token
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add loading indicator for route calculations
    if (config.url?.includes('routen-vorschlag') || config.url?.includes('route-details')) {
      console.log('🔄 Route calculation started...');
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle auth and errors
axiosClient.interceptors.response.use(
  (response) => {
    // Log successful route calculations
    if (response.config?.url?.includes('routen-vorschlag')) {
      console.log('✅ Route calculation completed successfully');
    }
    
    return response;
  },
  (error) => {
    // Enhanced error handling for Google Maps API issues
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          // Token expired
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          break;
          
        case 400:
          // Bad request - often API parameter issues
          console.error('❌ Request error:', data.detail || 'Invalid request parameters');
          break;
          
        case 429:
          // Rate limiting (Google Maps API)
          console.error('⚠️ API Rate limit exceeded. Please try again later.');
          break;
          
        case 500:
          // Server error
          console.error('🔥 Server error:', data.detail || 'Internal server error');
          break;
          
        default:
          console.error(`🚨 HTTP ${status}:`, data.detail || error.message);
      }
    } else if (error.request) {
      // Network error
      console.error('🌐 Network error: Unable to reach server');
    } else {
      // Other error
      console.error('❓ Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Specialized API methods for Google Maps integration
export const routeAPI = {
  // Calculate route suggestions with enhanced error handling
  calculateRoutes: async (startAddress) => {
    try {
      const response = await axiosClient.post('api/routen-vorschlag/', {
        start_adresse: startAddress,
      });
      return response.data;
    } catch (error) {
      // Enhanced error messages for route calculation
      if (error.response?.status === 400) {
        throw new Error(
          error.response.data.detail || 
          'Startadresse konnte nicht gefunden werden. Bitte überprüfen Sie Ihre Eingabe.'
        );
      }
      throw error;
    }
  },

  // Get detailed route information (replaces GraphHopper)
  getRouteDetails: async (start, destination, mode = 'walking') => {
    try {
      const response = await axiosClient.get('api/route-details/', {
        params: { start, ziel: destination, mode }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get route details:', error);
      throw error;
    }
  },

  // Geocode an address
  geocodeAddress: async (address) => {
    try {
      const response = await axiosClient.post('api/geocode/', {
        adresse: address
      });
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        throw new Error('Adresse konnte nicht gefunden werden.');
      }
      throw error;
    }
  },

  // Save a calculated route
  saveRoute: async (routeData) => {
    try {
      const response = await axiosClient.post('api/routen/speichern/', routeData);
      return response.data;
    } catch (error) {
      console.error('Failed to save route:', error);
      throw error;
    }
  }
};

// Profile and authentication API
export const profileAPI = {
  getProfile: async () => {
    const response = await axiosClient.get('api/profil/');
    return response.data;
  },

  register: async (userData) => {
    const response = await axiosClient.post('api/register/', userData);
    return response.data;
  }
};

// Data API for parkings, stadiums, etc.
export const dataAPI = {
  getParkings: async () => {
    const response = await axiosClient.get('api/parkplatz/');
    return response.data;
  },

  getStadiums: async () => {
    const response = await axiosClient.get('api/stadion/');
    return response.data;
  },

  getClubs: async () => {
    const response = await axiosClient.get('api/verein/');
    return response.data;
  },

  getRoutes: async () => {
    const response = await axiosClient.get('api/routen/');
    return response.data;
  }
};

// Utility function for retrying failed requests (useful for Google Maps API)
export const retryRequest = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      
      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
      console.log(`🔄 Retry attempt ${attempt}/${maxRetries}`);
    }
  }
};

export default axiosClient;