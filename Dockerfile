FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# 1. Install system tools and Python
RUN apt update && \
    apt install -y curl gnupg bash python3.10 python3-pip && \
    ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    rm -rf /var/lib/apt/lists/*

# 2. Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# 3. Set working directory
WORKDIR /app

# 4. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy project code
COPY ./app ./app
COPY ./static ./static

# 6. Copy startup script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 7. Expose necessary ports
EXPOSE 8000 11434

# 8. Start sequence: Ollama → pull model → FastAPI
ENTRYPOINT ["/entrypoint.sh"]

