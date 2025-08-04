# Use a lightweight Python base image
FROM python:3.12-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose the port Gunicorn will run on
EXPOSE 8000

# Run the application
CMD ["gunicorn", "timesheet.wsgi:application", "--bind", "0.0.0.0:8000"]
