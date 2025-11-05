import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "samqtcnjpkhfysgxbakn.supabase.co",
        port: "",
        pathname: "/storage/v1/object/public/**",
      },
    ],
  },
  async rewrites() {
    return [
      // Swagger UI (/docs)
      {
        source: "/docs",
        destination: "https://ai-meme-generator-backend.onrender.com/docs",
      },
      {
        source: "/docs/:path*",
        destination:
          "https://ai-meme-generator-backend.onrender.com/docs/:path*",
      },

      // ReDoc (/redoc)
      {
        source: "/redoc",
        destination: "https://ai-meme-generator-backend.onrender.com/redoc",
      },
      {
        source: "/redoc/:path*",
        destination:
          "https://ai-meme-generator-backend.onrender.com/redoc/:path*",
      },

      // OpenAPI schema (needed by Swagger UI)
      {
        source: "/openapi.json",
        destination:
          "https://ai-meme-generator-backend.onrender.com/openapi.json",
      },
    ];
  },
};

export default nextConfig;
