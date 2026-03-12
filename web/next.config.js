/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    // Proxy /api requests to the backend service
    // In Docker: backend is at http://backend:8000
    // Fallback: http://127.0.0.1:8000
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
      {
        source: '/docs',
        destination: `${backendUrl}/docs`,
      },
    ];
  },
}

module.exports = nextConfig
