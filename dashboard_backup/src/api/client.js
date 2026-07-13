import axios from 'axios'
import toast from 'react-hot-toast'
import { API_URL } from '../config'

// Create custom axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 seconds timeout
})

// Add Correlation ID request interceptor
apiClient.interceptors.request.use((config) => {
  config.headers['X-Correlation-ID'] = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(7)
  return config
})

// Add retry logic with exponential backoff response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config
    
    // Set max retries
    if (!config || !config.retry) {
      config.retry = 3
      config.retryCount = 0
    }
    
    if (config.retryCount < config.retry) {
      config.retryCount += 1
      const backoff = Math.pow(2, config.retryCount) * 1000 // exponential backoff
      
      console.warn(`Request failed. Retrying... (${config.retryCount}/${config.retry}) in ${backoff}ms`)
      
      await new Promise(resolve => setTimeout(resolve, backoff))
      return apiClient(config)
    }
    
    return Promise.reject(error)
  }
)

export const api = {
  predict: async (text, language = null) => {
    try {
      const response = await apiClient.post(`/predict`, { text, language })
      return response.data
    } catch (error) {
      toast.error(error.response?.data?.detail || "Prediction failed")
      throw error
    }
  },
  uploadBatch: async (file) => {
    try {
      const form = new FormData()
      form.append("file", file)
      const response = await apiClient.post(`/batch`, form)
      return response.data
    } catch (error) {
      toast.error(error.response?.data?.detail || "Batch upload failed")
      throw error
    }
  },
  getBatchStatus: async (jobId) => {
    const response = await apiClient.get(`/status/${jobId}`)
    return response.data
  },
  getHealth: async () => {
    const response = await apiClient.get(`/health`)
    return response.data
  }
}
