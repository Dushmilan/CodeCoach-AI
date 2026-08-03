FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies using npm
RUN npm install

# Copy source
COPY . .

# Build-time API URL for Next.js rewrites (Docker internal network).
# NEXT_PUBLIC_API_URL is intentionally NOT baked in: the client uses relative
# /api/* paths proxied to the backend by the rewrite, so it works identically
# on localhost and remote hosts (no absolute localhost:8000).
ENV API_URL=http://backend:8000
ENV NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Start
CMD ["npm", "start"]
