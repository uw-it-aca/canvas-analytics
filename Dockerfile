FROM acait/django-container:1.2.5 as app-container

USER root

RUN apt-get update && apt-get install mysql-client libmysqlclient-dev -y

USER acait

ADD --chown=acait:acait course_data/VERSION /app/course_data/
ADD --chown=acait:acait setup.py /app/
ADD --chown=acait:acait requirements.txt /app/
RUN . /app/bin/activate && pip install -r requirements.txt
RUN . /app/bin/activate && pip install mysqlclient

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ project/

RUN . /app/bin/activate && pip install nodeenv && nodeenv -p &&\
    npm install -g npm

FROM acait/django-test-container:1.2.5 as app-test-container

COPY --from=app-container /app/ /app/
COPY --from=app-container /static/ /static/
