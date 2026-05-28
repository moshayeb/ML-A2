# ============================================================
# DOCKERFILE -- Part 3: Mo-Assistant
# ============================================================
# Packages the agent into a container so it runs the same way
# on any machine or cloud server.
#
# Build:  docker build -t mo-assistant .
# Run:    docker run -e ANTHROPIC_API_KEY=your-key mo-assistant
#
# The API key is passed in at runtime with -e, NOT baked into
# the image -- this keeps secrets out of the container.
# ============================================================

# Use Python 3.11 as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy and install dependencies first (cached by Docker if unchanged)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files EXCEPT secrets (see .dockerignore)
COPY . .

# Run the agent
CMD ["python", "main.py"]
