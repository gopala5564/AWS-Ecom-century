FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY etl_processor.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the ETL process
CMD ["python", "etl_processor.py"]
