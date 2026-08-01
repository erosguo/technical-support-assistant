import axios from 'axios';

const TOKEN_KEY = 'tech_support_token';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Request interceptor — inject Authorization header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

export default api;
export { TOKEN_KEY };
