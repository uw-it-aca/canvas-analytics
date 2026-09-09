ARG DJANGO_CONTAINER_VERSION=3.1.4

FROM us-docker.pkg.dev/uwit-mci-axdd/containers/django-container:${DJANGO_CONTAINER_VERSION} AS app-container

USER root

RUN apt-get update && apt-get install -y freetds-bin freetds-dev

USER acait

COPY --chown=acait:acait . /app/
COPY --chown=acait:acait docker/ /app/project/

COPY --chown=acait:acait docker/app_start.sh /scripts
RUN chmod u+x /scripts/app_start.sh

RUN /app/bin/pip install -r requirements.txt

FROM us-docker.pkg.dev/uwit-mci-axdd/containers/django-test-container:${DJANGO_CONTAINER_VERSION} AS app-test-container

COPY --from=app-container /app/ /app/
