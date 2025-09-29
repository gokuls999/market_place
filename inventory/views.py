from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from .models import Products, Cart, CartItem, Users
from django_otp.plugins.otp_email.models import EmailDevice
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
    return render(request, 'products.html', {'products': products})

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
        try:
            user = Users.objects.create(
                username=username,
                email=email,
                phone=phone,
                password=make_password(password),
                role='customer',
                is_verified=False
            )
            print(f"DEBUG: User created - ID: {user.id}")
            # Email OTP
            email_otp = str(random.randint(100000, 999999))
            EmailDevice.objects.create(user=user, name='default', email=email, token=email_otp)
            send_mail(
                'Email OTP Verification',
                f'Your OTP is: {email_otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=True,
            )
            # Phone OTP (simulated via email)
            phone_otp = str(random.randint(100000, 999999))
            EmailDevice.objects.create(user=user, name='phone', email=phone + '@sms.example.com', token=phone_otp)
            send_mail(
                'Phone OTP Verification',
                f'Your OTP is: {phone_otp}',
                settings.EMAIL_HOST_USER,
                [phone + '@sms.example.com'],
                fail_silently=True,
            )
            print(f"DEBUG: Email OTP for {email}: {email_otp}")
            print(f"DEBUG: Phone OTP for {phone}: {phone_otp}")
            return redirect('verify_otp', user_id=user.id)
        except Exception as e:
            print(f"DEBUG: Error during registration: {str(e)}")
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'register.html')
    return render(request, 'register.html')

def verify_otp(request, user_id):
    user = get_object_or_404(Users, id=user_id)
    if request.method == 'POST':
        email_otp = request.POST.get('email_otp')
        phone_otp = request.POST.get('phone_otp')
        email_device = EmailDevice.objects.filter(user=user, name='default').first()
        phone_device = EmailDevice.objects.filter(user=user, name='phone').first()
        if email_device and phone_device and email_otp == email_device.token and phone_otp == phone_device.token:
            user.is_verified = True
            user.save()
            login(request, user)
            messages.success(request, 'Registration successful! You are now logged in.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid OTP.')
    return render(request, 'verify_otp.html', {'user_id': user_id})

# Create your views here.
