FROM python:3.11-alpine

LABEL org.label-schema.name="Eclipse BaSyx" \
      org.label-schema.version="1.0" \
      org.label-schema.description="Docker image for the basyx-python-sdk server application" \
      org.label-schema.maintainer="Eclipse BaSyx"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# If we have more dependencies for the server it would make sense
# to refactor uswgi to the pyproject.toml
RUN apk update && \
    apk add --no-cache nginx supervisor gcc musl-dev linux-headers python3-dev git bash && \
    pip install uwsgi && \
    pip install --no-cache-dir git+https://github.com/eclipse-basyx/basyx-python-sdk@main#subdirectory=sdk && \
    apk del git bash


COPY uwsgi.ini /etc/uwsgi/
COPY supervisord.ini /etc/supervisor/conf.d/supervisord.ini
COPY stop-supervisor.sh /etc/supervisor/stop-supervisor.sh
RUN chmod +x /etc/supervisor/stop-supervisor.sh

# Makes it possible to use a different configuration
ENV UWSGI_INI=/etc/uwsgi/uwsgi.ini
# object stores aren't thread-safe yet
# https://github.com/eclipse-basyx/basyx-python-sdk/issues/205
ENV UWSGI_CHEAPER=0
ENV UWSGI_PROCESSES=1
ENV NGINX_MAX_UPLOAD=1M
ENV NGINX_WORKER_PROCESSES=1
ENV LISTEN_PORT=80
ENV CLIENT_BODY_BUFFER_SIZE=1M

# Copy the entrypoint that will generate Nginx additional configs
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

COPY ./app /app
WORKDIR /app

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.ini"]
