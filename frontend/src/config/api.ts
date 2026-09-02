// Dynamic API and WebSocket endpoint resolver for Local, Render, and Vercel environments

export const getBackendUrls = () => {
  // 1. Explicit Vite Environment Variable (if provided in Vercel settings)
  const envBackendUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_URL;
  if (envBackendUrl) {
    const cleanUrl = envBackendUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
    const isHttps = envBackendUrl.startsWith('https://') || window.location.protocol === 'https:';
    return {
      httpBase: `${isHttps ? 'https' : 'http'}://${cleanUrl}`,
      wsBase: `${isHttps ? 'wss' : 'ws'}://${cleanUrl}`
    };
  }

  // 2. Local Development Server
  if (window.location.hostname === 'localhost' && window.location.port === '5173') {
    return {
      httpBase: 'http://localhost:8000',
      wsBase: 'ws://localhost:8000'
    };
  }

  // 3. Vercel Hosting (Connect to Render backend)
  if (window.location.hostname.includes('vercel.app')) {
    return {
      httpBase: 'https://railway-28.onrender.com',
      wsBase: 'wss://railway-28.onrender.com'
    };
  }

  // 4. Same-origin deployment (e.g. Render unified app)
  const isHttps = window.location.protocol === 'https:';
  return {
    httpBase: `${isHttps ? 'https' : 'http'}://${window.location.host}`,
    wsBase: `${isHttps ? 'wss' : 'ws'}://${window.location.host}`
  };
};

export const getApiUrl = (path: string) => {
  const { httpBase } = getBackendUrls();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${httpBase}${cleanPath}`;
};

export const getWsUrl = (path: string = '/ws/live') => {
  const { wsBase } = getBackendUrls();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${wsBase}${cleanPath}`;
};
