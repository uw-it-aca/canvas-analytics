#!/bin/bash

if [ "$ENV"  = "localdev" ]
then

  python manage.py migrate
  python manage.py create_or_update_courses
  python manage.py create_assignment_jobs
  python manage.py create_participation_jobs

fi