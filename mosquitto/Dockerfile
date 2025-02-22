ARG version=latest

FROM eclipse-mosquitto

WORKDIR /

RUN apk add --no-cache tzdata && \
    rm -rf /var/cache/apk/* && \
    touch /mosquitto/config/.passwords && \
    chmod 600 /mosquitto/config/.passwords && \
    chown root /mosquitto/config/.passwords