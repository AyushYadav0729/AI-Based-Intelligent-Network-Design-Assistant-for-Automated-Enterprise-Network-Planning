/**
 * client.js — Axios API client for the FastAPI backend.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// System
export const getHealth = () => api.get('/health')
export const getCatalog = () => api.get('/catalog')

// Design & Validation
export const generateDesign = (requirements) => api.post('/design/generate', requirements)
export const validateDesign = (design, requirements) => api.post('/design/validate', { design, requirements })

// Persistence (Projects)
export const getProjects = () => api.get('/projects')
export const getProject = (id) => api.get(`/projects/${id}`)
export const saveProject = (payload) => api.post('/projects', payload)
export const deleteProject = (id) => api.delete(`/projects/${id}`)
export const compareProjects = (ids) => api.get(`/projects/compare?ids=${ids.join(',')}`)

export default api
