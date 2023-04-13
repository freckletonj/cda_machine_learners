# Use the official Python 3.9 image as the base image
FROM python:3.9

# Copy the requirements file into the container
COPY requirements.txt .

# Install any required packages
RUN pip install --no-cache-dir -r requirements.txt

# Add entrypoint scripts
ADD /docker/entrypoints /entrypoints
RUN chmod -R +x /entrypoints

# Set the working directory
WORKDIR /app
# Copy the rest of the application code
COPY src .