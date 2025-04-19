from django.shortcuts import render,redirect,get_object_or_404
from .models import Product
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.views.decorators.http import require_POST


from django.contrib.auth.decorators import login_required
from .models import CustomUser,Product, Order, OrderItem, Wishlist, Cart
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import reverse
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from rent.models import Rent

# Create your views here.
def signup_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('signup')

        user = CustomUser.objects.create_user(name=name, email=email, password=password, role=role)
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')
    return render(request, 'signup.html')



def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('main')  # Use the correct name for the main page route
        else:
            messages.error(request, "Invalid email or password")
            return redirect('login')  # Redirect back to the login page
    return render(request, 'login.html')


def homepageFunction(request):
        return render(request,"homepage.html")
def mainpageFunction(request):
    context = {}
    
    # Only fetch sales data if user is authenticated and is a seller
    if request.user.is_authenticated and request.user.role == "seller":
        # Get the period from query parameters (default to 'week')
        period = request.GET.get('period', 'week')
        
        # Calculate date range based on period
        today = timezone.now().date()
        if period == 'week':
            start_date = today - timedelta(days=7)
            period_display = "Week"
        elif period == 'month':
            start_date = today - timedelta(days=30)
            period_display = "Month"
        else:  # year
            start_date = today - timedelta(days=365)
            period_display = "Year"
        
        # Get all orders for the seller within the date range
        seller_orders = OrderItem.objects.filter(
            product__seller=request.user,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=today
        )
        
        # Calculate daily sales
        daily_sales = {}
        total_sales = 0
        best_day = None
        best_day_sales = 0
        
        # Initialize all days in the period with zero sales
        current_date = start_date
        while current_date <= today:
            day_name = current_date.strftime('%a')  # Abbreviated day name (Mon, Tue, etc.)
            daily_sales[day_name] = {'value': 0, 'percentage': 10}  # Default 10% height for zero sales
            current_date += timedelta(days=1)
        
        # Count sales for each day
        for order in seller_orders:
            order_date = order.order.created_at.date()
            day_name = order_date.strftime('%a')
            
            # Update the count for this day
            daily_sales[day_name]['value'] += order.quantity
            total_sales += order.quantity
            
            # Check if this is the best day so far
            if daily_sales[day_name]['value'] > best_day_sales:
                best_day = day_name
                best_day_sales = daily_sales[day_name]['value']
        
        # Calculate percentage heights for the chart (max 100%)
        max_daily_sales = max([data['value'] for data in daily_sales.values()]) if daily_sales else 1
        for day, data in daily_sales.items():
            if max_daily_sales > 0:
                data['percentage'] = min(100, int((data['value'] / max_daily_sales) * 100))
        
        # Calculate average daily sales
        days_in_period = (today - start_date).days + 1
        avg_daily_sales = round(total_sales / days_in_period, 1) if days_in_period > 0 else 0
        
        # Get top selling products
        top_products = OrderItem.objects.filter(
            product__seller=request.user,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=today
        ).values('product__name').annotate(
            sold_count=Sum('quantity')
        ).order_by('-sold_count')[:5]
        
        # Calculate demand percentage for each product
        max_sold = top_products[0]['sold_count'] if top_products else 1
        for product in top_products:
            product['demand_percentage'] = min(100, int((product['sold_count'] / max_sold) * 100))
        
        # Since there's no Review model, create some sample reviews
        customer_reviews = [
            {
                'name': 'John Doe',
                'product': 'Modern Dining Table',
                'rating': 5,
                'comment': 'The dining table is exactly as described. The quality is excellent and it was delivered on time. Very satisfied with the purchase!'
            },
            {
                'name': 'Jane Smith',
                'product': 'Leather Sofa Set',
                'rating': 4,
                'comment': 'The sofa set is comfortable and looks great in my living room. The delivery was a bit delayed, but the product quality makes up for it.'
            },
            {
                'name': 'Sarah Lee',
                'product': 'Wooden Bookshelf',
                'rating': 5,
                'comment': 'The bookshelf is sturdy and well-made. It was easy to assemble and looks perfect in my home office. Highly recommend!'
            }
        ]
        
        # Add all data to context
        context = {
            'daily_sales': daily_sales,
            'total_sales': total_sales,
            'avg_daily_sales': avg_daily_sales,
            'best_day': best_day,
            'best_day_sales': best_day_sales,
            'period': period_display,
            'top_products': top_products,
            'customer_reviews': customer_reviews
        }
    
    return render(request, "mainpage.html", context)
@login_required
def productFunction(request):
    search_query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '')
    
    # Base queryset - show only seller's products if logged in as seller
    if request.user.role == "seller":
        products = Product.objects.filter(seller=request.user)
    else:
        products = Product.objects.all()
    
    # Apply search filter if query exists
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    # Apply category filter
    if category:
        products = products.filter(category=category)
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-id')
    
    # Get unique categories for filter
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category,
        'selected_sort': sort_by
    }
    
    return render(request, 'Product.html', context)
@login_required
def aboutFunction(request):
        return render(request,"Aboutus.html")
@login_required
def contactFunction(request):
        return render(request,"Contact.html")

def sellerFunction(request):
     if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        image_url = request.POST.get('image_url')
        category = request.POST.get('category')

        # Save product with current user as seller
        Product.objects.create(
            seller=request.user,
            name=name,
            description=description,
            price=price,
            stock=stock,
            image_url=image_url,
            category=category
        )
        messages.success(request, "Product submitted successfully!")
        return redirect('all_products')

     return render(request,"seller.html")



def place_order_view(request):
    if request.method == 'POST':
        product_id = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantities')
        
        if not product_id:
            return render(request, 'place_order.html', {
                'products': Product.objects.all(),
                'error': 'Please select at least one product.'
            })

        total = 0
        items = []

        for product_id, quantity in zip(product_id, quantities):
            product = Product.objects.get(id=product_id)
            quantity = int(quantity)
            total += product.price * quantity
            items.append((product, quantity))
            payment_method = request.POST.get('payment_method')
        address = request.POST.get('address')

        if not payment_method or not address:
            return render(request, 'place_order.html', {
                'products': Product.objects.all(),
                'error': 'Payment method and address are required.'
            })



        # Create the order
        order = Order.objects.create(buyer=request.user, total=Decimal(total))

        # Create order items
        for product, quantity in items:
            OrderItem.objects.create(order=order, product=product, quantity=quantity)

        return redirect('user_dashboard')  # After order, go to dashboard

    # GET request — show product list to select from
    products = Product.objects.all()
    return render(request, 'product.html', {'products': products})

def category_view(request, category_slug):
    products = Product.objects.filter(category=category_slug)
    return render(request, 'Product.html', {
        'products': products,
        'category': category_slug.replace('-', ' ').title()
    })
def buy_now_view(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        return render(request, 'buynow.html', {'product': product})
    else:
        return render(request, 'buynow.html', {'error': 'Invalid request'})
@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, pk=product_id)
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)

            if product_id_str in cart:
                cart[product_id_str]['quantity'] += 1
                message = f"Quantity updated for {product.name}"
            else:
                cart[product_id_str] = {
                    'name': product.name,
                    'price': float(product.price),
                    'image_url': product.image_url if product.image_url else '',
                    'quantity': 1
                }
                message = f"{product.name} added to your cart"

            request.session['cart'] = cart
            return JsonResponse({
                'success': True,
                'message': message,
                'redirect': reverse('cart')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = {}
    total=0

    for product_id, item in cart.items():
        subtotal = item['price'] * item['quantity']
        total += subtotal
        cart_items[product_id] = {
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'image_url': item.get('image_url'),
            'subtotal': f"{subtotal:.2f}"
        }

    return render(request, 'cart.html', {'cart_items': cart_items,'total':f"{total:.2f}"})

def remove_from_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)

        if product_id_str in cart:
            del cart[product_id_str]
            request.session['cart'] = cart
            messages.success(request, 'Item removed from cart.')
        else:
            messages.warning(request, 'Item not found in cart.')

    return redirect('cart')

@require_POST
def update_quantity(request, product_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)

        if product_id_str in cart:
            if action == 'increase':
                cart[product_id_str]['quantity'] += 1
            elif action == 'decrease':
                cart[product_id_str]['quantity'] -= 1
                if cart[product_id_str]['quantity'] <= 0:
                    del cart[product_id_str]

        request.session['cart'] = cart

    return redirect('cart')  # 🔁 
def checkout_view(request):
    cart = request.session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())

    if request.method == 'POST':
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        
        # Create the order with payment method and address
        order = Order.objects.create(
            buyer=request.user,
            total=Decimal(total),
            payment_method=payment_method,
            address=address
        )
        
        # Create order items
        for product_id_str, item in cart.items():
            try:
                product = Product.objects.get(id=int(product_id_str))
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['quantity']
                )
            except Product.DoesNotExist:
                continue

        # Clear the cart after placing the order
        request.session['cart'] = {}
        
        messages.success(request, 'Order placed successfully!')
        return redirect('order_place')  # Changed from 'profile' to 'pro_file'

    return render(request, 'checkout.html', {'total': total})
def order_place(request):
     return render(request,'orderplace.html')
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    name = request.user.name
    email = request.user.email
    role = request.user.role
    
    context = {
        'name': name,
        'email': email,
        'role': role,
    }
    
    if role == 'buyer':
        # Get purchase history
        orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
        purchase_details = []
        total_spent = 0
        
        for order in orders:
            for item in order.items.all():
                purchase_details.append({
                    'name': item.product.name,
                    'price': item.product.price,
                    'quantity': item.quantity,
                    'total': item.product.price * item.quantity
                })
                total_spent += item.product.price * item.quantity
        
        context.update({
            'purchase_details': purchase_details,
            'total_spent': total_spent
        })
        
        # Get rental history
        from rent.models import Rental
        from datetime import date
        
        rentals = Rental.objects.filter(user=request.user).order_by('-start_date')
        today = date.today()
        
        context.update({
            'rentals': rentals,
            'today': today
        })
        
    elif role == 'seller':
        # Get seller's products
        seller_products = Product.objects.filter(seller=request.user)
        context['seller_products'] = seller_products
    
    return render(request, 'profile.html', context)


    # Ensure the logged-in user has a profile and filter their orders


def logout_view(request):
    logout(request)
    return redirect('main')

@login_required
def add_to_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Check if item already in wishlist
            if Wishlist.objects.filter(user=request.user, product=product).exists():
                return JsonResponse({
                    'success': False,
                    'message': f"{product.name} is already in your wishlist."
                })
            
            # Create new wishlist item
            Wishlist.objects.create(user=request.user, product=product)
            return JsonResponse({
                'success': True,
                'message': f"{product.name} added to your wishlist."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def remove_from_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            wishlist_item = get_object_or_404(Wishlist, user=request.user, product=product)
            product_name = product.name
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'message': f"{product_name} removed from your wishlist."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def view_wishlist(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.role == "seller":
        # For sellers, show wishlist items only for their own products
        wishlist_items = Wishlist.objects.filter(
            user=request.user,
            product__seller=request.user
        ).select_related('product')
    else:
        # For buyers, show all their wishlist items
        wishlist_items = Wishlist.objects.filter(
            user=request.user
        ).select_related('product')
    
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'wishlist.html', context)

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    return render(request, 'product_detail.html', {
        'product': product,
        'in_wishlist': in_wishlist
    })
@login_required
def product_list(request):
    if request.user.role != 'seller':
        return redirect('homepage')
    
    # Get seller's products with additional details
    seller_products = Product.objects.filter(seller=request.user)
    
    # Get order statistics for each product
    products_with_stats = []
    for product in seller_products:
        # Get total orders for this product
        total_orders = OrderItem.objects.filter(product=product).count()
        
        # Get total quantity sold
        total_quantity = OrderItem.objects.filter(product=product).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        # Get total revenue
        total_revenue = OrderItem.objects.filter(product=product).aggregate(
            total=Sum(F('quantity') * F('product__price'))
        )['total'] or 0
        
        # Get wishlist count
        wishlist_count = Wishlist.objects.filter(product=product).count()
        
        products_with_stats.append({
            'product': product,
            'total_orders': total_orders,
            'total_quantity': total_quantity,
            'total_revenue': total_revenue,
            'wishlist_count': wishlist_count
        })
    
    # Print debug information
    print(f"Seller ID: {request.user.id}")
    print(f"Seller Email: {request.user.email}")
    print(f"Number of products found: {seller_products.count()}")
    print(f"Number of products with stats: {len(products_with_stats)}")
    
    context = {
        'products_with_stats': products_with_stats,
        'name': request.user.name,
        'email': request.user.email,
        'role': request.user.role
    }
    return render(request, 'product_list.html', context)
def list_view(request):
    return redirect('seller_product_list')
@login_required
def update_product(request, id):
    # Retrieve the product, ensuring the logged-in user is the seller
    product = get_object_or_404(Product, id=id, seller=request.user)

    # Check if it's a POST request (form submission)
    if request.method == 'POST':
        # Get data from the form and update the product instance
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.image_url = request.POST.get('image_url')

        # Save the updated product
        product.save()

        # Redirect to the product list page after update
        return redirect('all_products')  # Assuming 'product_list' is your URL for the product listing page
    else:
        # If it's a GET request, just render the form with current data
        return render(request, 'update.html', {'product': product})
def delete_product(request, id):
    # Retrieve the product to delete, ensuring the logged-in user is the seller
    product = get_object_or_404(Product, id=id, seller=request.user)

    # Delete the product
    product.delete()

    # Redirect to the product list page after deletion
    return redirect('all_products')  #

from django.utils.text import slugify
from django.http import JsonResponse

def search_ajax(request):
    query = request.GET.get('q', '').strip().lower()
    
    CATEGORY_SLUGS = {
        'desks': 'Desks',
        'office-chairs': 'Office Chairs',
        'paintings': 'Paintings',
        'coffee-tables': 'Coffee Tables',
        'sofa-couches': 'Sofa and Couches',
        'bookshelves': 'Bookshelves',
        'side-tables': 'Side Tables',
        'dining-tables': 'Dining Tables',
        'dining-chairs': 'Dining Chairs',
        'buffets-and-sideboards': 'Buffets and Sideboards',
        'bar-carts': 'Bar Carts',
        'file-cabinets': 'File Cabinets',
        'wall clocks': 'Wall Clocks',
        'doormats': 'Doormats',
        'fairy lights': 'Fairy Lights',
        'others': 'Others',
        # Add more categories as needed
    }

    # Normalize keys to remove spaces for matching
    normalized_category_slugs = {
        category_slug.replace(' ', '-').lower(): category_name
        for category_slug, category_name in CATEGORY_SLUGS.items()
    }

    # Check for a match
    if query in normalized_category_slugs:
        return JsonResponse({'url': f'/category/{query}/'})

    # Return default if no match
    return JsonResponse({'url': '/'})


@login_required
def wishlist_statistics(request):
    # Check if the user is a seller
    if request.user.role != 'seller':
        return redirect('main')
    
    # Get all products added to wishlists that belong to the current seller
    wishlist_items = Wishlist.objects.filter(product__seller=request.user)
    
    # Create a dictionary to count how many times each product is in wishlists
    product_wishlist_count = {}
    for item in wishlist_items:
        product_id = item.product.id
        if product_id in product_wishlist_count:
            product_wishlist_count[product_id] += 1
        else:
            product_wishlist_count[product_id] = 1
    
    # Get all products with their wishlist counts (only for the current seller)
    products_with_counts = []
    for product in Product.objects.filter(seller=request.user):
        wishlist_count = product_wishlist_count.get(product.id, 0)
        products_with_counts.append({
            'product': product,
            'wishlist_count': wishlist_count
        })
    
    # Sort products by wishlist count (highest first)
    products_with_counts.sort(key=lambda x: x['wishlist_count'], reverse=True)
    
    context = {
        'products_with_counts': products_with_counts
    }
    
    return render(request, 'wishlist_statistics.html', context)

@login_required
def sales_overview(request):
    if request.user.role != 'seller':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get time period from query params, default to week
    period = request.GET.get('period', 'week')
    
    # Calculate start date based on period
    today = datetime.now().date()
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    else:  # year
        start_date = today - timedelta(days=365)
    
    # Get all orders for the seller's products within the date range
    seller_orders = Order.objects.filter(
        items__product__seller=request.user,
        created_at__date__gte=start_date,
        created_at__date__lte=today
    ).distinct()
    
    # Calculate daily sales
    daily_sales = []
    for i in range((today - start_date).days + 1):
        current_date = start_date + timedelta(days=i)
        day_total = seller_orders.filter(
            created_at__date=current_date
        ).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        daily_sales.append({
            'day': current_date.strftime('%a'),
            'amount': float(day_total)
        })
    
    # Calculate total sales
    total_sales = seller_orders.aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Calculate average daily sales
    avg_daily_sales = total_sales / len(daily_sales) if daily_sales else 0
    
    # Find best sales day
    best_day = max(daily_sales, key=lambda x: x['amount'])
    
    # Get top products
    top_products = OrderItem.objects.filter(
        order__in=seller_orders,
        product__seller=request.user
    ).values(
        'product__name',
        'product__price'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('product__price'))
    ).order_by('-total_quantity')[:5]
    
    # Format top products data
    top_products_data = [{
        'name': item['product__name'],
        'quantity': item['total_quantity'],
        'revenue': float(item['total_revenue'])
    } for item in top_products]
    
    # Get customer reviews (if you have a review model, add it here)
    # For now, we'll use a placeholder
    customer_reviews = []
    
    context = {
        'daily_sales': daily_sales,
        'total_sales': float(total_sales),
        'avg_daily_sales': float(avg_daily_sales),
        'best_day': best_day,
        'top_products': top_products_data,
        'customer_reviews': customer_reviews,
        'period': period
    }
    
    return render(request, 'sales_overview.html', context)

@login_required
def seller_dashboard(request):
    if request.user.role != 'seller':
        return redirect('homepage')
    
    # Get seller's products
    products = Product.objects.filter(seller=request.user)
    
    # Get recent orders for seller's products
    recent_orders = OrderItem.objects.filter(
        product__seller=request.user
    ).select_related('order', 'product').order_by('-order__created_at')[:5]
    
    # Calculate total sales for seller's products
    total_sales = OrderItem.objects.filter(
        product__seller=request.user
    ).aggregate(
        total=Sum(F('product__price') * F('quantity'))
    )['total'] or 0
    
    # Get top selling products for this seller
    top_products = OrderItem.objects.filter(
        product__seller=request.user
    ).values(
        'product__name'
    ).annotate(
        total=Sum('quantity')
    ).order_by('-total')[:5]
    
    context = {
        'products': products,
        'recent_orders': recent_orders,
        'total_sales': total_sales,
        'top_products': top_products,
    }
    
    return render(request, 'seller_dashboard.html', context)

def search_products(request):
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'url': '/'})
    
    # Search in product names and descriptions
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    )
    
    if products.exists():
        # If products found, redirect to products page with search query
        return JsonResponse({'url': f'/product/?search={query}'})
    
    # Check if query matches any category
    CATEGORY_SLUGS = {
        'desks': 'Desks',
        'office-chairs': 'Office Chairs',
        'paintings': 'Paintings',
        'coffee-tables': 'Coffee Tables',
        'sofa-couches': 'Sofa and Couches',
        'bookshelves': 'Bookshelves',
        'side-tables': 'Side Tables',
        'dining-tables': 'Dining Tables',
        'dining-chairs': 'Dining Chairs',
        'buffets-and-sideboards': 'Buffets and Sideboards',
        'bar-carts': 'Bar Carts',
        'file-cabinets': 'File Cabinets',
        'wall-clocks': 'Wall Clocks',
        'doormats': 'Doormats',
        'fairy-lights': 'Fairy Lights',
        'others': 'Others',
    }
    
    # Normalize query and category slugs for comparison
    normalized_query = query.lower().replace(' ', '-')
    normalized_categories = {
        slug.replace(' ', '-').lower(): name
        for slug, name in CATEGORY_SLUGS.items()
    }
    
    if normalized_query in normalized_categories:
        return JsonResponse({'url': f'/category/{normalized_query}/'})
    
    # If no matches found, redirect to products page with search query
    return JsonResponse({'url': f'/product/?search={query}'})