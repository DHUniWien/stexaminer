from django.contrib import admin

# To leverage the automatic form-creation and model management of Django, we'll have to register our model here

from .models import Calc

admin.site.register(Calc)




