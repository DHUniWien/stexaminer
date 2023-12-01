#import pymysql
from .celery import celery_app

#pymysql.install_as_MySQLdb()

# this code snippet imports Celery every time our application starts:
__all__ = ['celery_app']