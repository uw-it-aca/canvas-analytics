#!/bin/bash

if [ "$ENV"  = "localdev" ]
then

  python manage.py migrate
  python manage.py loaddata mock_data.json

fi