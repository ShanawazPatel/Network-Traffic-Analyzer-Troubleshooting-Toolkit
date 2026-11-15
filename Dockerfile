FROM python:3.12-slim

# Install system networking tools and iptables
RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables \
    iproute2 \
    iputils-ping \
    tcpdump \
    curl \
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "netpulse", "health"]
