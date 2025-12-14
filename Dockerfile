# Multi-stage build: smaller final image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt 

# Copy the entire project
COPY . .
