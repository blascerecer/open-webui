FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Expose the API port
EXPOSE 8081

# Run the application
CMD ["python", "-m", "mcp_bridge_manager.main"]