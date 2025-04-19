from django.urls import path
from .views import rent_product_view,rent,product_list1,submit_rent_product,rent_product,rental_success,rent_view,seller_listed_products,rental_history

app_name = 'rent'

urlpatterns = [
    path('rent', rent, name='rent'),
    path('submit/', submit_rent_product, name='submit_rent_product'),
    path('products/', product_list1, name='product_list1'),
    path('seller-listed-products/', seller_listed_products, name='seller_listed_products'),
    path('rent-item/<int:product_id>/', rent_product, name='rent_product'),
    path('rental-success/', rental_success, name='rental_success'),
    path('view/', rent_view, name='rent_view'),
    path('rent/<int:product_id>/', rent_product_view, name='rent_product_view'),
    path('rental_history/', rental_history, name='rental_history'),
]
 