FROM debian:bookworm-slim

RUN apt update && apt upgrade -y
RUN apt install -y python3-venv python3-pip git

# Install debian-package-repository
COPY dist/*.whl /etc/effective-range/debian-package-repository/
RUN python3 -m venv venv
RUN venv/bin/pip install /etc/effective-range/debian-package-repository/*.whl

# Copy keys
COPY tests/keys/* /etc/effective-range/debian-package-repository/keys/

# Start debian-package-repository
ENTRYPOINT venv/bin/python3 venv/bin/debian-package-repository.py \
--private-key-path /etc/debian-package-repository/keys/private-key.asc \
--public-key-path /etc/debian-package-repository/keys/public-key.asc "$@"
