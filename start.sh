#!/bin/bash

# CodeCoach AI - Quick Start Script
# This script helps you deploy the application locally or to cloud

set -e

echo "🚀 CodeCoach AI - Deployment Helper"
echo "===================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker found"

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    exit 1
fi

echo "✅ Docker Compose found"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "📝 Please edit .env and add your NVIDIA_API_KEY"
    echo "   Get your free key: https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct"
    echo ""
    read -p "Press Enter after you've added your API key..."
fi

# Check if NVIDIA_API_KEY is set
if grep -q "your_nvidia_nim_api_key_here" .env; then
    echo "⚠️  NVIDIA_API_KEY is still set to default value"
    echo "   Please edit .env and add your actual API key"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to cancel..."
fi

echo ""
echo "🔨 Building and starting services..."
echo ""

# Start services
docker compose up --build -d

echo ""
echo "✅ Services started!"
echo ""
echo "📊 Checking service health..."
sleep 5

# Check if services are running
echo ""
echo "🔍 Service Status:"
docker compose ps

echo ""
echo "🎉 Your CodeCoach AI is running!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Piston:    http://localhost:2000"
echo ""
echo "📝 Useful commands:"
echo "   View logs:     docker compose logs -f"
echo "   Stop:          docker compose down"
echo "   Restart:       docker compose restart"
echo "   Rebuild:       docker compose up --build"
echo ""
