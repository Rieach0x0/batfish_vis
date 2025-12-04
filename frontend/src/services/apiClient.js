/**
 * Base API client service with fetch wrapper and error handling.
 *
 * Provides centralized HTTP communication with the backend API.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * API error class for structured error handling.
 */
export class ApiError extends Error {
  constructor(message, status, code, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/**
 * Execute HTTP request with error handling.
 *
 * @param {string} endpoint - API endpoint path (relative to API_BASE_URL)
 * @param {object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<any>} Response data
 * @throws {ApiError} On HTTP errors or network failures
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  // Only set Content-Type: application/json if not explicitly overridden
  // For FormData, we should NOT set Content-Type (browser sets it automatically)
  const defaultHeaders = {};
  if (options.body && !(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    console.debug(`API Request: ${config.method || 'GET'} ${url}`);

    const response = await fetch(url, config);

    // Parse response body
    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    // Handle HTTP errors
    if (!response.ok) {
      const error = data?.error || 'Request failed';
      const message = data?.message || response.statusText;
      const code = data?.code || 'UNKNOWN_ERROR';

      console.error(`API Error: ${response.status} ${error}`, { url, message, code });

      throw new ApiError(message, response.status, code, data);
    }

    console.debug(`API Response: ${response.status}`, data);
    return data;

  } catch (error) {
    // Re-throw ApiError
    if (error instanceof ApiError) {
      throw error;
    }

    // Network or fetch errors
    console.error('Network error:', error);
    throw new ApiError(
      'Network error - could not reach the server',
      0,
      'NETWORK_ERROR',
      { originalError: error.message }
    );
  }
}

/**
 * API client object with HTTP methods.
 */
const apiClient = {
  /**
   * GET request
   */
  async get(endpoint, params = null) {
    let url = endpoint;
    if (params) {
      const query = new URLSearchParams(params).toString();
      url = `${endpoint}?${query}`;
    }
    return request(url, { method: 'GET' });
  },

  /**
   * POST request with JSON body
   */
  async post(endpoint, body = null) {
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  /**
   * POST request with FormData (for file uploads)
   */
  async postForm(endpoint, formData) {
    return request(endpoint, {
      method: 'POST',
      body: formData, // FormData will be detected and Content-Type will not be set
    });
  },

  /**
   * PUT request with JSON body
   */
  async put(endpoint, body = null) {
    return request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  },

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return request(endpoint, { method: 'DELETE' });
  },

  /**
   * Health check endpoint
   */
  async healthCheck() {
    return this.get('/health');
  },
};

export default apiClient;
