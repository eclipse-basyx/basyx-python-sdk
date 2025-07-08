FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# If we have more dependencies for the server it would make sense
# to refactor uswgi to the pyproject.toml
RUN apk update && \
    apk add --no-cache nginx supervisor gcc musl-dev linux-headers python3-dev git bash && \
    pip install uwsgi && \
    apk del git bash


COPY registry_server/uwsgi.ini /etc/uwsgi/
COPY registry_server/supervisord.ini /etc/supervisor/conf.d/supervisord.ini
COPY registry_server/stop-supervisor.sh /etc/supervisor/stop-supervisor.sh
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
COPY registry_server/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

ENV SETUPTOOLS_SCM_PRETEND_VERSION=1.0.0


COPY ./registry_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./sdk /sdk
COPY ./server /server
COPY ./registry_server/app /app

WORKDIR /app
RUN pip install ../sdk

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.ini"]