import axios from 'axios'
import Cookies from 'js-cookie'

const API = axios.create({
  baseURL: 'http://localhost:8000', // adjust for production as needed
})

// Automatically attach JWT to every request if present
API.interceptors.request.use(config => {
  const token = Cookies.get('token')
  if (token) {
    // Ensure headers object exists
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default API