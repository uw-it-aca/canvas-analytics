#!/bin/bash

if [ "$ENV"  = "localdev" ]
then

  python manage.py migrate
  python manage.py loaddata mock_courses.json
  python manage.py loaddata mock_jobs.json

fi