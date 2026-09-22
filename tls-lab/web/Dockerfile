FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        openssl curl iproute2 traceroute \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY server.py .

# Self-signed cert for the lab "bank" site (CN does not matter for the exercise)
RUN openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/CN=lab-pank.local"

EXPOSE 80 443
CMD ["python3", "server.py"]
