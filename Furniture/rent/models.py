from django.db import models
from user.models import Product, CustomUser
from django.conf import settings  
class Rent(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='rentals')
    renter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rentals')
    daily_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.renter.username}"

    def save(self, *args, **kwargs):
        # Calculate total price based on number of days
        days = (self.end_date - self.start_date).days
        self.total_price = self.daily_price * days
        super().save(*args, **kwargs)

class RentableProduct(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rentable_products')
    image_url = models.URLField(max_length=500)  # Image URL of the product
    product_name = models.CharField(max_length=255)  # Name of the product
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)  # Condition of the product
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)  # Price per day for renting
    
    def __str__(self):
        return self.product_name

class Rental(models.Model):
    rentable_product = models.ForeignKey(RentableProduct, on_delete=models.CASCADE)  
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)# Link to the rentable product
    start_date = models.DateField()  # Start date of the rental
    end_date = models.DateField()  # End date of the rental
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Total price for the rental

    def __str__(self):
        return f"Rental for {self.rentable_product.product_name} from {self.start_date} to {self.end_date}"