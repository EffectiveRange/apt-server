ARG SERVER_ARCH=$SERVER_ARCH
ARG IMAGE_REPO=${SERVER_ARCH}/debian
ARG IMAGE_VER=bullseye-slim

FROM ${IMAGE_REPO}:${IMAGE_VER}

RUN apt update && apt upgrade -y

# Install apt-server
COPY dist/*.deb /etc/apt-server/
RUN apt install -y /etc/apt-server/*.deb

ARG CLIENT_ARCH=$CLIENT_ARCH
ENV ARCHITECTURES=${CLIENT_ARCH}

# Start apt-server
CMD /opt/venvs/apt-server/bin/python3 /opt/venvs/apt-server/bin/apt-server.py \
     --architectures ${ARCHITECTURES}                                         \
     --release-template /opt/venvs/apt-server/templates/Release.template      \
     --signing-key-path /opt/venvs/apt-server/.gnupg/private-key.asc          \
     --public-key-path /opt/venvs/apt-server/.gnupg/public-key.asc
