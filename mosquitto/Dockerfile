ARG version=latest

FROM eclipse-mosquitto

WORKDIR /

RUN apk add --no-cache tzdata && \
    rm -rf /var/cache/apk/*
