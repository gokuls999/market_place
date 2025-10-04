from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from .models import Products, Cart, CartItem, Users
from django_otp.plugins.otp_email.models import EmailDevice
from django.db.models import Q
from .models import Categories
import random
def product_detail(request, product_id):
    product = get_object_or_404(Products, id=product_id, approved=True)
    return render(request, 'product_detail.html', {'product': product})
def home(request):
    products = Products.objects.filter(approved=True)[:6]  # Fetch up to 6 approved products
    return render(request, 'home.html', {'products': products})
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Products, id=product_id, approved=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')
@login_required
def cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    return render(request, 'cart.html', {'cart': cart})

def products(request):
    products = Products.objects.filter(approved=True)
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    if category_id:
        products = products.filter(category_id=category_id)
    categories = Categories.objects.all()
    return render(request, 'products.html', {'products': products, 'search_query': search_query, 'category_id': category_id, 'categories': categories})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_verified:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Please verify your email and phone OTPs.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return render(request, 'logout.html')

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['password']
        print(f"DEBUG: Received registration - Username: {username}, Email: {email}, Phone: {phone}")
        if Users.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'register.html')
        if Users.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'register.html')
        # Store data in session for verification
        request.session['registration_data'] = {
            'username': username,
            'email': email,
            'phone': phone,
            'password': password,
        }
        # Generate and send email OTP
        email_otp = str(random.randint(100000, 999999))
        request.session['email_otp'] = email_otp
        send_mail(
            'Email OTP Verification',
            f'Your OTP is: {email_otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=True,
        )
        print(f"DEBUG: Email OTP for {email}: {email_otp}")
        return redirect('verify_otp')
    return render(request, 'register.html')

def verify_otp(request):
    if request.method == 'POST':
        email_otp = request.POST.get('email_otp')
        registration_data = request.session.get('registration_data')
        session_otp = request.session.get('email_otp')
        if not registration_data or not session_otp:
            messages.error(request, 'Session expired. Please register again.')
            return redirect('register')
        if email_otp == session_otp:
            # Create user after successful OTP
            username = registration_data['username']
            email = registration_data['email']
            phone = registration_data['phone']
            password = registration_data['password']
            user = Users.objects.create(
                username=username,
                email=email,
                phone=phone,
                password=make_password(password),
                role='customer',
                is_verified=True  # Set verified since OTP passed
            )
            print(f"DEBUG: User created after OTP - ID: {user.id}")
            # Clear session
            del request.session['registration_data']
            del request.session['email_otp']
            login(request, user)
            messages.success(request, 'Registration successful! You are now logged in.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid OTP.')
    return render(request, 'verify_otp.html')

# Create your views here.
