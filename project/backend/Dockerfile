FROM python:3.11-slim

# Prevent Python from writing pyc files to disc and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# - build-essential and unixodbc-dev are needed to compile pyodbc if needed
# - libgomp1 is required by xgboost
# - gnupg2, curl, and apt-transport-https are used to add the MS SQL repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg2 \
    apt-transport-https \
    unixodbc-dev \
    libgomp1 \
    pkg-config \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft SQL Server ODBC Driver 17 repositories (optional but standard for pyodbc + MS SQL)
RUN mkdir -p /usr/share/keyrings \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft-2025.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/13/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 mssql-tools \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy dependency file first to leverage Docker cache
COPY requirements.txt ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Start FastAPI via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
