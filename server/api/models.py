from django.db import models

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return self.title

class Company(models.Model):
    exp_dates = models.CharField(max_length=20, null=True)
    high = models.FloatField(null=True)
    low = models.FloatField(null=True)

    #def __str__(self):
        #return self.exp_dates

    def __float__(self):
        return self.high