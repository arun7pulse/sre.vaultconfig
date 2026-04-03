# Use the official lightweight Python image.
FROM python:3.10-slim

# Immediately flush stdout/stderr so logs appear in Docker output.
ENV PYTHONUNBUFFERED=True

# Default port (override with -e PORT=<n> at runtime).
ENV PORT=5000

# Working directory inside the container.
ENV APP_HOME=/app
WORKDIR $APP_HOME

# Copy source and install dependencies.
COPY . ./
RUN pip install --no-cache-dir -r requirements.txt

# Expose the API port.
EXPOSE $PORT

# Run with gunicorn: 1 worker, 8 threads.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 app:app"]