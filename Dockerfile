# Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create app directory if it doesn't exist
RUN mkdir -p app/routes app/utils

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "run.py"]