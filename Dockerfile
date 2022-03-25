FROM gcr.io/uwit-mci-axdd/django-container:1.3.8 as app-prewebpack-container

USER root

RUN apt-get update && apt-get install libpq-dev -y
RUN apt-get update && apt-get install freetds-bin -y

USER acait

ADD --chown=acait:acait data_aggregator/VERSION /app/data_aggregator/
ADD --chown=acait:acait setup.py /app/
ADD --chown=acait:acait requirements.txt /app/
RUN . /app/bin/activate && pip install --upgrade pip
RUN . /app/bin/activate && pip install -r requirements.txt

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ project/
ADD --chown=acait:acait docker/app_start.sh /scripts
RUN chmod u+x /scripts/app_start.sh

RUN . /app/bin/activate && pip install django-webpack-loader

FROM node:8.15.1-jessie AS wpack
ADD . /app/
WORKDIR /app/
RUN npm install .
RUN npx webpack --mode=production

FROM app-prewebpack-container as app-container

COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/data_aggregator/bundles/* /app/data_aggregator/static/data_aggregator/bundles/
COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/ /static/
COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/webpack-stats.json /app/data_aggregator/static/webpack-stats.json

FROM gcr.io/uwit-mci-axdd/django-test-container:1.3.8 as app-test-container

COPY --from=app-container /app/ /app/
COPY --from=app-container /static/ /static/
