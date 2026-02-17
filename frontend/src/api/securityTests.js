import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': import.meta.env.VITE_API_KEY || 'test-api-key-1'
  }
})

export const securityTestAPI = {
  getScenarios: () => api.get('/scenarios'),
  
  runTest: (data) => api.post('/security-tests/run', data),
  
  getTestStatus: (testId) => api.get(`/security-tests/${testId}/status`),
  
  getTestResults: (testId) => api.get(`/security-tests/${testId}`),
  
  generateVariants: (data) => api.post('/variants/generate', data),
  
  getVariantsByPrompt: (promptId) => api.get(`/variants/by-prompt/${promptId}`),
  
  getTestAnalytics: (testId) => api.get(`/analytics/test/${testId}/summary`),
  
  getVendorComparison: () => api.get('/analytics/vendor-comparison'),
  
  getComplianceDashboard: () => api.get('/analytics/compliance-dashboard')
}

export default api