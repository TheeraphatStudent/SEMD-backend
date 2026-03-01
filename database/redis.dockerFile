FROM docker.io/library/redis:latest

COPY config/redis.conf /usr/local/etc/redis/redis.conf

EXPOSE 6379

RUN mkdir -p /var/log/redis \
    && chown redis:redis /var/log/redis

CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]
