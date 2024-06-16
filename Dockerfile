FROM debian:bookworm-slim

RUN apt update && apt upgrade -y

# Install apt-server
COPY dist/*.deb /etc/apt-server/
RUN apt install -y /etc/apt-server/*.deb
ENV PATH="/opt/venvs/apt-server/bin:$PATH"

# Copy keys
COPY tests/keys/* /etc/apt-server/keys/

# Set package architectures
ARG PACKAGE_ARCHS=$PACKAGE_ARCHS
ENV ARCHITECTURES=${PACKAGE_ARCHS}

# Start apt-server
CMD apt-server.py --port 80 --architectures ${ARCHITECTURES} \
--private-key-path /etc/apt-server/keys/private-key.asc \
--public-key-path /etc/apt-server/keys/public-key.asc
