import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  output: 'standalone',
  transpilePackages: [
    '@xyflow/react',
    '@xyflow/system',
    'reactflow',
    '@dnk/teleprompter-core',
    '@dnk/video-audit-core'
  ],
  webpack: (config, { isServer, webpack }) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'reactflow': '@xyflow/react',
    };
    config.resolve.extensionAlias = {
      '.js': ['.ts', '.tsx', '.js', '.jsx'],
    };
    config.resolve.modules.push(path.resolve(__dirname, 'node_modules'));

    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        child_process: false,
        crypto: false,
        util: false,
        path: false,
        stream: false,
        os: false,
      };

      config.plugins.push(
        new webpack.NormalModuleReplacementPlugin(
          /^node:/,
          (resource) => {
            resource.request = resource.request.replace(/^node:/, '');
          }
        )
      );
    }
    return config;
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    const backendHost =
      process.env.BACKEND_INTERNAL_URL ||
      process.env.BACKEND_URL ||
      (process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://127.0.0.1:8000');
    return [
      {
        source: '/api/:path*',
        destination: `${backendHost}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
