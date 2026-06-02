/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack(config) {
    config.output.uniqueName = "notesgram-frontend";
    return config;
  },
};

module.exports = nextConfig;