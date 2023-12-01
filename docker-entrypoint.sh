#!/bin/bash

# Wait for MySQL to come up
echo "######### waiting 60 secs for MySQL to come up #########"
now=$(date)
echo $now
sleep 60 
echo "######### waiting finihed #########"
now=$(date)
echo $now

# Do the necessary DB migrations
echo "######### Doing database migrations #########"
cd /home/idp
echo "# Pack model changes into a file #"
#python manage.py makemigrations
python manage.py makemigrations api_app
echo "# Apply those changes to the database #"
#python manage.py migrate --run-syncdb
python manage.py migrate    ### what is the difference to above?!

# Start celery worker
echo "######### Starting Celery worker #########"
celery -A idp3_async_api_djproj worker &
#celery -A idp3_async_api_djproj worker --loglevel=DEBUG &
#celery -A idp3_async_api_djproj worker --config=settings &     ### Error: No such option: --config

# Start Django server
echo "######### Starting Django server #########"
python manage.py runserver 0.0.0.0:8000
