# Use Python 3.11 as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy all project files
COPY . .

# Run the agent
CMD ["python", "-c", "print('Mo-Assistant container ready!')"]