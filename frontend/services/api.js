const API_BASE_URL = 'http://127.0.0.1:5000';

export const searchAPI = async (query) => {
  const response = await fetch(`${API_BASE_URL}/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
};

export const chatAPI = async (message, conversationHistory = []) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: message,
      conversation_history: conversationHistory,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
};

export const mapAPI = async (namaste_code, k = 3) => {
  // Try GET endpoint with query params (server may accept either GET /map?query=... or POST /map)
  const url = `${API_BASE_URL}/map?query=${encodeURIComponent(namaste_code)}&k=${encodeURIComponent(k)}`;
  let response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  // If GET is not supported (e.g., 404/405), fallback to POST
  if (!response.ok && (response.status === 404 || response.status === 405)) {
    response = await fetch(`${API_BASE_URL}/map`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ namaste_code, k }),
    });
  }

  if (!response.ok) {
    // Try to extract JSON error detail if available
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
  }

  return await response.json();
};