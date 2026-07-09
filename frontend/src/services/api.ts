import axios from 'axios';

// API Base Configuration
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// API Interface Definitions

// Returned immediately by POST /upload - processing happens in the background.
export interface UploadAcceptedResponse {
  task_id: string;
  file_id: string;
  filename: string;
  status: string;
  message: string;
}

// The full processing result, available once the background task finishes.
export interface TaskResult {
  document_id: string;
  filename: string;
  saved_path: string;
  content_length: number;
  file_type: string;
  status: string;
  extraction_result: any;
  storage_result: any;
  message: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: 'processing' | 'completed' | 'failed';
  result?: TaskResult;
  error?: string;
}

// Kept for components that render a merged { ...accepted, ...result } object
// once processing completes (see FileUpload.tsx).
export interface UploadResponse extends TaskResult {
  file_id: string;
}

export interface SearchResponse {
  results: any[];
  error?: string;
}

export interface GraphData {
  nodes: any[];
  links: any[];
  error?: string;
}

export interface EntitiesResponse {
  entities: any[];
  error?: string;
}

export interface HealthResponse {
  status: string;
  database: string;
}

// API Methods
export const apiService = {
  // Health Check
  async checkHealth(): Promise<HealthResponse> {
    const response = await api.get('/health');
    return response.data;
  },

  // File Upload - returns a task id immediately, processing runs in the background
  async uploadFile(file: File): Promise<UploadAcceptedResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Poll the status of a background processing task
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  // Search Entities
  async searchEntities(query: string): Promise<SearchResponse> {
    const response = await api.get('/search', {
      params: { q: query },
    });
    return response.data;
  },

  // Get Graph Data
  async getGraphData(limit: number = 100): Promise<GraphData> {
    const response = await api.get('/graph', {
      params: { limit },
    });
    return response.data;
  },

  // Get All Entities
  async getEntities(limit: number = 50): Promise<EntitiesResponse> {
    const response = await api.get('/entities', {
      params: { limit },
    });
    return response.data;
  },
};

export default api;
