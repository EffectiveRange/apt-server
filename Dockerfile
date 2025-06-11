FROM debian:bookworm-slim

RUN apt update && apt upgrade -y
RUN apt install -y python3-venv python3-pip git

# Install apt-server
COPY dist/*.whl /etc/apt-server/
RUN python3 -m venv venv
RUN venv/bin/pip install /etc/apt-server/*.whl

# Copy keys
COPY tests/keys/* /etc/apt-server/keys/

# Start apt-server
ENTRYPOINT venv/bin/python3 venv/bin/apt-server.py \
--private-key-path /etc/apt-server/keys/private-key.asc \
--public-key-path /etc/apt-server/keys/public-key.asc "$@"
