FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        dsniff tcpdump iproute2 iptables net-tools curl openssl \
        python3 python3-pip tshark \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir mitmproxy

CMD ["sleep", "infinity"]
