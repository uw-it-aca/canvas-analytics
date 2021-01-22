FROM acait/django-container:1.2.5 as app-container

USER root

RUN apt-get update && apt-get install mysql-client libmysqlclient-dev -y

USER acait

ADD --chown=acait:acait data_aggregator/VERSION /app/data_aggregator/
ADD --chown=acait:acait setup.py /app/
ADD --chown=acait:acait requirements.txt /app/
RUN . /app/bin/activate && pip install -r requirements.txt
RUN . /app/bin/activate && pip install mysqlclient

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ project/

RUN . /app/bin/activate && pip install nodeenv && nodeenv -p &&\
    npm install -g npm

ADD --chown=acait:acait docker/app_start.sh /scripts
RUN chmod u+x /scripts/app_start.sh

FROM node:8.15.1-jessie AS wpack
ADD . /app/
WORKDIR /app/
RUN npm install .
RUN npx webpack --mode=production

FROM app-container

COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/data_aggregator/bundles/* /app/data_aggregator/static/data_aggregator/bundles/
COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/ /static/
COPY --chown=acait:acait --from=wpack /app/data_aggregator/static/webpack-stats.json /app/data_aggregator/static/webpack-stats.json

FROM acait/django-test-container:1.2.5 as app-test-container

COPY --from=app-container /app/ /app/
COPY --from=app-container /static/ /static/
