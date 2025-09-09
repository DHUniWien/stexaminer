from django.urls import path
from .views import CalcRequest
from .views import AddRequest
from .views import jobstatus
from .views import delete_from_database
from django.conf.urls import url

#print ("\n########## urls.py ##############\n")

urlpatterns = [
    path('calc-items/', CalcRequest.as_view()),
    path('add-items/', AddRequest.as_view()),
    #path('jobstatus/', jobstatus.as_view()),    ### AttributeError: 'function' object has no attribute 'as_view'
    ### [PF:] as_view() works only with classes!!
    #url(r'^%s/jobstatus/(?P<run_id>\d+)/$' % 'calc-items', jobstatus, name = 'jobstatus_url')
    ###  [PF:] use re_path [=~ regular expression path] instead of url(r'^%s/j....    
    path("jobstatus/<int:run_id>/", jobstatus, name='jobstatus_url'),
    path("delete_from_database/<int:run_id>/", delete_from_database, name='delete_from_database_url')
]
