from django.contrib import admin

# Register your models here.

from .models import Trainee, Trainer, Appointment, Membership

admin.site.register(Trainee)
admin.site.register(Trainer)
admin.site.register(Appointment)
admin.site.register(Membership)

admin.site.site_header = "Elite Fitness Administration"
admin.site.site_title = "Elite Gym Admin"
admin.site.index_title = "Dashboard Overview"