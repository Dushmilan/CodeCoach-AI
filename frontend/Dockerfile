# syntax=docker/dockerfile:1.6
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies using npm with BuildKit cache (saves data on rebuilds)
RUN --mount=type=cache,target=/root/.npm npm install

# Copy source
COPY . .

# Build-time API URL for Next.js rewrites (Docker internal network)
ARG API_URL=http://backend:8000
# Client-side API URLs: empty default = same-origin via the /api rewrite
# (CSP-safe). Set an absolute https: URL only for cross-origin deployments.
ARG NEXT_PUBLIC_API_URL=
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000
ENV API_URL=$API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Start
CMD ["npm", "start"]
