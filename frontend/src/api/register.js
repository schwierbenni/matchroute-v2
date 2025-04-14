import axiosClient from './axiosClient';

export const registerUser = (data) => {
  return axiosClient.post('/parkplatz/register/', data);
};