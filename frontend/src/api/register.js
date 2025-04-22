import axiosClient from './axiosClient';

export const registerUser = (data) => {
  return axiosClient.post('/api/register/', data);
};