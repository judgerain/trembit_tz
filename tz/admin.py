from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Course)
admin.site.register(models.Student)
admin.site.register(models.CourseParticipant)
