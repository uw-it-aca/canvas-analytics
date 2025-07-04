ARG DJANGO_CONTAINER_VERSION=2.0.8

FROM us-docker.pkg.dev/uwit-mci-axdd/containers/django-container:${DJANGO_CONTAINER_VERSION} AS app-prewebpack-container

USER root

RUN apt-get update && apt-get install libpq-dev freetds-bin -y

USER acait

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ /app/project/

ADD --chown=acait:acait docker/app_start.sh /scripts
RUN chmod u+x /scripts/app_start.sh

RUN /app/bin/pip install -r requirements.txt
RUN /app/bin/pip install django-webpack-loader psycopg2

FROM node:8.15.1-jessie AS wpack
ADD . /app/
WORKDIR /app/
RUN npm install .
RUN npx webpack --mode=production

FROM app-prewebpack-container AS app-container

COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/data_aggregator/bundles/* /app/data_aggregator/static/data_aggregator/bundles/
COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/ /static/
COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/webpack-stats.json /app/data_aggregator/static/webpack-stats.json

FROM us-docker.pkg.dev/uwit-mci-axdd/containers/django-test-container:${DJANGO_CONTAINER_VERSION} AS app-test-container

COPY --from=app-container /app/ /app/
COPY --from=app-container /static/ /static/
