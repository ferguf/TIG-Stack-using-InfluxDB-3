# File: ./python/Dockerfile

# Use a stable, lightweight Python image
FROM python:3.11-slim

# Set environment variables for better logging/performance
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
# Set the working directory inside the container
# This directory (/app) will be the root for your Uvicorn command
WORKDIR /app

# Copy the requirements file and install dependencies
# This is a critical step for installing 'fastmcp'
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./python/requirements.txt $APP_HOME/python/
RUN pip install --no-cache-dir -r $APP_HOME/python/requirements.txt

# Copy all the application code into the working directory
# This includes the 'api/' and 'mcp_tools/' directories
COPY . /app/

# The port FastAPI runs on
EXPOSE 8000

# Command to run the application (matches your docker-compose command)
# This starts the combined FastAPI/FastMCP server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]