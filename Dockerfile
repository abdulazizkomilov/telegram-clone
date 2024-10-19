FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/opt/venv

# Install apt-utils and other necessary dependencies
RUN apt-get update && apt-get install -y \
    apt-utils curl netcat vim gettext python3-venv \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a virtual environment for Python dependencies
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set the working directory
WORKDIR /telegram_app

# Copy project files
COPY . /telegram_app/

# Install Python dependencies in the virtual environment
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script and make it executable
COPY .deploy/entrypoint.sh /
RUN chmod +x /entrypoint.sh

# Expose the application port
EXPOSE 8000

# Define entrypoint
ENTRYPOINT ["sh", "/entrypoint.sh"]
