FROM debian:latest

RUN apt-get update && apt-get install -y \
    bash \
    htop \
    vim \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m nonroot

USER nonroot

ENV OWNER="Aymen"


CMD ["sleep", "3600"]

