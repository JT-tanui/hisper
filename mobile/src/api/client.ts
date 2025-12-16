import axios from 'axios';
import Constants from 'expo-constants';

const apiClient = axios.create({
  baseURL: Constants.expoConfig?.extra?.apiUrl ?? 'https://api.hisper.local',
  timeout: 8000
});

export { apiClient };
