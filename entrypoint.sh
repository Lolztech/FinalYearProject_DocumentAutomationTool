#!/bin/bash

# Start Ollama in background
OLLAMA_HOST=0.0.0.0 ollama serve &

# Wait for Ollama to be ready
until curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "Waiting for Ollama to become ready..."
  sleep 1
done

# Pull the model (one-time)
ollama pull llama3:8b

# Now start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000