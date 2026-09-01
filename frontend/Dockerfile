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
# Client-side API URLs (resolve via Docker host port mapping)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000
# Supabase client config (baked into the OAuth callback page)
ARG NEXT_PUBLIC_SUPABASE_URL=
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY=
ENV API_URL=$API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Start
CMD ["npm", "start"]
