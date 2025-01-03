from django.db import models
from django.contrib.auth.models import User
import os
# Create your models here.
# Dynamic path for CSVs
def user_csv_path(instance, filename):
    # Assuming `instance.user.username` exists
    return f'user_media/{instance.user.username}/csv/{filename}'

# Dynamic path for charts
def user_chart_path(instance, filename):
    return f'user_media/{instance.user.username}/charts/{filename}'

class ProductDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link data to a specific user
    product_name = models.CharField(max_length=255)
    price_comparison = models.FileField(upload_to=user_csv_path)
    price_distribution_chart = models.ImageField(upload_to=user_chart_path)
    amazon_data = models.FileField(upload_to=user_csv_path)
    flipkart_data = models.FileField(upload_to=user_csv_path)
    amazon_stats = models.JSONField()  # Store stats as JSON
    flipkart_stats = models.JSONField()  # Store stats as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product_name}"