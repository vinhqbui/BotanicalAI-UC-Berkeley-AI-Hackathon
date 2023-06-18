from django.db import models

class Organization(models.Model):
    name = models.CharField(max_length=200, verbose_name='Company name')
    date_created = models.DateField(auto_now_add=True)
    description = models.CharField(max_length=400)
    last_active = models.DateField(auto_now_add=True)


class Users(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    date_created = models.DateField(auto_now_add=True)
    last_active = models.DateField(auto_now_add=True)
    access_level = models.PositiveIntegerField(verbose_name='Access Level')

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    

class Data(models.Model):
    title = models.CharField(max_length=200)
    data = models.FileField(upload_to=None) # Update later

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
