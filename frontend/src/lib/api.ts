import axios from 'axios'
import Cookies from 'js-cookie'

const API = axios.create({
  baseURL: 'http://localhost:8000', // Adjust to production backend endpoint
})

// Automatically attach JWT if present
API.interceptors.request.use(config => {
  const token = Cookies.get('token')
  if (token) config.headers!['Authorization'] = `Bearer ${token}`
  return config
})

export default API