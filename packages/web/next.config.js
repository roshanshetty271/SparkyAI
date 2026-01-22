/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  },
  
  // Allow images from external sources
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  
  // Webpack configuration for D3.js
  webpack: (config) => {
    // D3 uses ES modules, ensure proper handling
    config.resolve.alias = {
      ...config.resolve.alias,
      'd3': 'd3',
    };
    return config;
  },
};

module.exports = nextConfig;
