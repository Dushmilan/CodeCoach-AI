FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies using npm
RUN npm install

# Copy source
COPY . .

# Build-time API URL for Next.js rewrites (Docker internal network)
ENV API_URL=http://backend:8000
# Client-side API URL (resolves via Docker host port mapping)
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Start
CMD ["npm", "start"]
