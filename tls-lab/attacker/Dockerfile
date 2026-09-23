FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        # Protsessihaldus (ps, top, pkill jms)
        procps \
        # Võrgudiagnostika ja ühenduste vaatamine (ss, ip)
        iproute2 \
        net-tools \
        # Paketianalüüs ja liikluse pealtkuulamine
        tcpdump \
        tshark \
        ngrep \
        # MITM ja võrgutööriistad
        dsniff \
        iptables \
        dnsutils \
        netcat-openbsd \
        nmap \
        curl \
        openssl \
        # Terminalimugavused logide/pakettide sirvimiseks
        less \
        vim-tiny \
        # Python ja mitmproxy
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir mitmproxy

CMD ["sleep", "infinity"]
