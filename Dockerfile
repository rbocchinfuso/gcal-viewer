FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY calendar_searcher_html.py .
COPY app.py .

# Create output directory
RUN mkdir -p /app/output

# Create credentials directory (will be mounted)
RUN mkdir -p /app/credentials

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SEARCH_QUERY=moto
ENV SEARCH_DAYS=30
ENV TZ=UTC

# Expose Flask port
EXPOSE 5000

# Run the Flask app with scheduler
CMD ["python", "app.py"]
