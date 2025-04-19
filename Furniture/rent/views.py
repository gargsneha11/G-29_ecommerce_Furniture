from django.shortcuts import render, redirect, get_object_or_404
from .models import Rent # Adjust if your Product model is elsewhere
from django.contrib.auth.decorators import login_required
from datetime import  date
from django.contrib import messages
from .models import RentableProduct
from .models import Rental # Assuming your Product model is in products app
from .forms import RentForm ,RentalForm
from datetime import datetime
from datetime import timedelta
from django.db import models
from .decorators import buyer_required, seller_required



@buyer_required
def rent_product_view(request, product_id):
    product = get_object_or_404(RentableProduct, id=product_id)

    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            if start_date >= end_date:
                form.add_error('end_date', 'End date must be after start date.')
            else:
                rental_days = (end_date - start_date).days
                total_price = rental_days * product.price_per_day

                Rental.objects.create(
                    user=request.user, 
                    rentable_product=product,
                    start_date=start_date,
                    end_date=end_date,
                    total_price=total_price
                )
                messages.success(request, 'Product rented successfully!')
                return redirect('rent:rental_success')  # Redirect to the rental success page
    else:
        form = RentalForm()

    return render(request, 'rent_product.html', {
        'product': product,
        'form': form
    })

def rent(request):
    return render(request,'rent_form.html')

@seller_required
def submit_rent_product(request):
    if request.method == 'POST':
        # Get data from the form and save it to the database
        image_url = request.POST.get('image_url')
        product_name = request.POST.get('product_name')
        condition = request.POST.get('condition')
        price_per_day = request.POST.get('price_per_day')

        # Create and save the product object
        RentableProduct.objects.create(
            user=request.user,
            image_url=image_url,
            product_name=product_name,
            condition=condition,
            price_per_day=price_per_day
        )
        
        messages.success(request, 'Product listed successfully!')
        return redirect('rent:seller_listed_products')  # Redirect to the seller's products page
    
    return render(request, 'submit_rent_product.html')

# View to display the list of rentable products as cards
@login_required
def product_list1(request):
    products = RentableProduct.objects.all()  # Fetch all products
    return render(request, 'product_list1.html', {'products': products})

@buyer_required
def rent_product(request, product_id):
    product = get_object_or_404(RentableProduct, id=product_id)

    if request.method == 'POST':
        form = RentForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            if start_date >= end_date:
                form.add_error('end_date', 'End date must be after start date.')
            else:
                rental_days = (end_date - start_date).days
                total_price = rental_days * product.price_per_day

                Rental.objects.create(
                    user=request.user, 
                    rentable_product=product,
                    start_date=start_date,
                    end_date=end_date,
                    total_price=total_price
                )
                messages.success(request, 'Product rented successfully!')
                return redirect('rent:rental_success')
    else:
        form = RentForm()

    return render(request, 'user_form.html', {
        'product': product,
        'form': form,
    })

def rental_success(request):
    return render(request, 'rental_success.html')

def rent_view(request):
    # Get the period from query parameters, default to 'week'
    period = request.GET.get('period', 'week')
    
    # Calculate date range based on period
    today = date.today()
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())  # Start of the week
        end_date = start_date + timedelta(days=6)  # End of the week
    elif period == 'month':
        start_date = today.replace(day=1)  # Start of the month
        end_date = today  # End of the current month
    else:  # year
        start_date = today.replace(month=1, day=1)  # Start of the year
        end_date = today  # End of the current year
    
    # Get all rentals for the seller's products
    seller_products = RentableProduct.objects.filter(user=request.user)
    rentals = Rental.objects.filter(
        rentable_product__in=seller_products,
        start_date__gte=start_date,
        start_date__lte=end_date
    ).order_by('-start_date')
    
    # Calculate rental summary
    total_rentals = rentals.count()
    total_revenue = sum([rental.total_price for rental in rentals])
    avg_duration = total_rentals and sum([(rental.end_date - rental.start_date).days for rental in rentals]) / total_rentals or 0
    
    # Get active rentals (currently rented out)
    active_rentals = Rental.objects.filter(
        rentable_product__in=seller_products,
        end_date__gte=today
    ).count()
    
    # Get upcoming rentals (starting in the next 7 days)
    upcoming_rentals = Rental.objects.filter(
        rentable_product__in=seller_products,
        start_date__gt=today,
        start_date__lte=today + timedelta(days=7)
    ).count()
    
    # Get the most rented products within the period
    rented_products = Rental.objects.filter(
        rentable_product__in=seller_products,
        start_date__gte=start_date,
        start_date__lte=end_date
    ).values('rentable_product').annotate(
        total_rentals=models.Count('rentable_product'),
        total_revenue=models.Sum('total_price')
    ).order_by('-total_rentals')[:5]
    
    # Get product details for the most rented products
    top_rented_products = []
    for product_data in rented_products:
        product = RentableProduct.objects.get(id=product_data['rentable_product'])
        product.total_rentals = product_data['total_rentals']
        product.total_revenue = product_data['total_revenue']
        product.demand_percentage = (product_data['total_rentals'] / total_rentals * 100) if total_rentals > 0 else 0
        top_rented_products.append(product)
    
    # Get recent renters with more details
    recent_rentals = Rental.objects.filter(
        rentable_product__in=seller_products
    ).select_related('user', 'rentable_product').order_by('-start_date')[:5]
    
    # Calculate rental status distribution
    status_distribution = {
        'active': Rental.objects.filter(
            rentable_product__in=seller_products,
            end_date__gte=today
        ).count(),
        'completed': Rental.objects.filter(
            rentable_product__in=seller_products,
            end_date__lt=today
        ).count(),
        'upcoming': Rental.objects.filter(
            rentable_product__in=seller_products,
            start_date__gt=today
        ).count()
    }
    
    context = {
        'period': period,
        'total_rentals': total_rentals,
        'total_revenue': total_revenue,
        'avg_duration': round(avg_duration, 1),
        'active_rentals': active_rentals,
        'upcoming_rentals': upcoming_rentals,
        'top_rented_products': top_rented_products,
        'recent_rentals': recent_rentals,
        'status_distribution': status_distribution,
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'rent_view.html', context)

@seller_required
def seller_listed_products(request):
    # Get all products listed by the current seller
    seller_products = RentableProduct.objects.filter(user=request.user).order_by('-id')
    
    # Get rental information for each product
    for product in seller_products:
        product.active_rentals = Rental.objects.filter(
            rentable_product=product,
            end_date__gte=date.today()
        ).count()
        product.total_rentals = Rental.objects.filter(rentable_product=product).count()
    
    return render(request, 'seller_listed_products.html', {
        'products': seller_products
    })

@buyer_required
def rental_history(request):
    # Get all rentals for the current user
    rentals = Rental.objects.filter(user=request.user).order_by('-start_date')
    
    # Get today's date for status comparison
    today = date.today()
    
    return render(request, 'rental_history.html', {
        'rentals': rentals,
        'today': today
    })