from django.db import models

# Create your models here.
class FuelStation(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=200)
    lat = models.FloatField()
    lon = models.FloatField()
    price = models.FloatField()  # price per gallon in USD

    def __str__(self):
        return f"{self.name} ({self.price})"
