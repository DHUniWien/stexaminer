#!/bin/bash

cd /home/idp
# Wait for the database if necessary
if [ -n "${STEX_DBHOST}" ]; then
    dbport=$STEX_DBPORT
    if [ -z "${STEX_DBPORT}" ]; then
        case $STEX_DBENGINE in
            mysql)
            dbport="3306"
            ;;
            postgresql_psycopg2)
            dbport="5432"
            ;;
        esac
    fi
    now=$(date)
    echo $now
    echo "Waiting for ${STEX_DBHOST}:${dbport} to come online"
    ./wait-for-it.sh "${STEX_DBHOST}:${dbport}" -t 60 -- echo "######### Initialising Stexaminer #########"
fi

# Do the necessary DB migrations
echo "######### Doing database migrations #########"
cd /home/idp
echo "### Pack model changes into a file ###"
#python manage.py makemigrations
python manage.py makemigrations api_app
echo "### Apply those changes to the database ###"
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
