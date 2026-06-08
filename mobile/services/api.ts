/**
 * Backend API client for Smart Baggage Architect mobile app.
 */

declare const __DEV__: boolean;

const API_BASE_URL = __DEV__
  ? 'http://10.0.2.2:8000'
  : 'https://api.smartbaggagearchitect.com';

interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = API_BASE_URL + endpoint;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      return { data: null, error: error.detail || response.statusText };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (err) {
    return { data: null, error: err instanceof Error ? err.message : 'Network error' };
  }
}

// Trip endpoints
export const createTrip = (tripData: Record<string, unknown>) =>
  request<Record<string, unknown>>('/api/trip/', {
    method: 'POST',
    body: JSON.stringify(tripData),
  });

export const getTrip = (tripId: string) =>
  request<Record<string, unknown>>('/api/trip/' + tripId);

export const listTrips = () =>
  request<Record<string, unknown>[]>('/api/trip/');

export const deleteTrip = (tripId: string) =>
  request<Record<string, unknown>>('/api/trip/' + tripId, { method: 'DELETE' });

// Packing endpoints
export const getPackingList = (tripId: string) =>
  request<Record<string, unknown>>('/api/packing/' + tripId);

export const updatePackingItem = (tripId: string, itemId: string, update: Record<string, unknown>) =>
  request<Record<string, unknown>>('/api/packing/' + tripId + '/item/' + itemId, {
    method: 'PUT',
    body: JSON.stringify(update),
  });

export const markItemDetected = (tripId: string, itemId: string) =>
  request<Record<string, unknown>>('/api/packing/' + tripId + '/item/' + itemId + '/detect', {
    method: 'POST',
  });

export const optimizePacking = (tripId: string) =>
  request<Record<string, unknown>>('/api/packing/' + tripId + '/optimize', { method: 'POST' });

export const regeneratePackingList = (tripId: string) =>
  request<Record<string, unknown>>('/api/packing/regenerate/' + tripId, { method: 'POST' });

// Airline endpoints
export const listAirlines = () =>
  request<Record<string, unknown>>('/api/airline/');

export const getAirlinePolicy = (iataCode: string) =>
  request<Record<string, unknown>>('/api/airline/' + iataCode);

// Weather endpoints
export const getWeatherSummary = (city: string, days: number = 7) =>
  request<Record<string, unknown>>(
    '/api/weather/summary?city=' + encodeURIComponent(city) + '&days=' + days
  );

export const getClothingRecommendations = (city: string) =>
  request<Record<string, unknown>>(
    '/api/weather/recommendations?city=' + encodeURIComponent(city)
  );

// LLM endpoints
export const getPackingAdvice = (data: Record<string, unknown>) =>
  request<Record<string, unknown>>('/api/llm/advice', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getCustomsAlert = (destination: string, origin: string = 'US') =>
  request<Record<string, unknown>>('/api/llm/customs-alert', {
    method: 'POST',
    body: JSON.stringify({ destination, origin }),
  });

// Feedback endpoints
export const submitFeedback = (data: Record<string, unknown>) =>
  request<Record<string, unknown>>('/api/feedback/item', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const submitMissingEssential = (data: Record<string, unknown>) =>
  request<Record<string, unknown>>('/api/feedback/missing', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getAdaptiveProfile = (destination: string, activityType: string = 'leisure') =>
  request<Record<string, unknown>>(
    '/api/feedback/adaptive/' + encodeURIComponent(destination) + '?activity_type=' + activityType
  );

// Vision endpoints
export const detectItems = (imageUri: string) => {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'scan.jpg',
  } as any);
  return request<Record<string, unknown>>('/api/vision/detect', {
    method: 'POST',
    headers: { 'Content-Type': 'multipart/form-data' },
    body: formData,
  });
};

export const healthCheck = () => request<{ status: string }>('/health');

export default {
  createTrip,
  getTrip,
  listTrips,
  deleteTrip,
  getPackingList,
  updatePackingItem,
  markItemDetected,
  optimizePacking,
  regeneratePackingList,
  listAirlines,
  getAirlinePolicy,
  getWeatherSummary,
  getClothingRecommendations,
  getPackingAdvice,
  getCustomsAlert,
  submitFeedback,
  submitMissingEssential,
  getAdaptiveProfile,
  detectItems,
  healthCheck,
};