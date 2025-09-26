# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies needed for some Python packages (e.g., if using psycopg2 or other packages)
# Combine RUN commands for efficiency and to minimize layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port your Flask app will run on
EXPOSE 5000

# Set environment variables (if needed)
ENV FLASK_APP=index.py
ENV FLASK_ENV=production

# Run the Flask application
# CMD ["flask", "run", "--host=0.0.0.0"]
CMD ["/usr/local/bin/gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "index:app"]