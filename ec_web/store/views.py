from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from store.models import Product, Order, OrderItem, Customer, Category
from store.models import Payment as PaymentModel
from django.conf import settings
from django.http import JsonResponse
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_redirect_customer(request):
    """Returns (customer, None) or (None, redirect_response)"""
    try:
        return Customer.objects.get(user=request.user), None
    except Customer.DoesNotExist:
        return None, redirect('complete_profile')

def profile_required(view_func):
    """Redirects to complete_profile if Customer profile doesn't exist yet."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if not Customer.objects.filter(user=request.user).exists():
                return redirect('complete_profile')
        return view_func(request, *args, **kwargs)
    return wrapper

def store(request):
    if not request.session.get('cart'):
        request.session['cart'] = {}

    categories = Category.get_all_categories()
    category_id = request.GET.get('category')
    search_query = request.GET.get('search', '').strip()
    products = Product.get_all_products()

    if search_query:
        products = products.filter(name__icontains=search_query)
    if category_id:
        products = products.filter(category_id=category_id)

    if request.GET.get('format') == 'suggestions':
        results = list(products.values('name', 'price')[:6])
        return JsonResponse({'suggestions': results})

    return render(request, 'index.html', {
        'products':      products,
        'categories':    categories,
        'search_query':  search_query,
        'category_id':   category_id,
    })


class Index(View):
    def post(self, request):
        product = request.POST.get('product')
        remove = request.POST.get('remove')
        cart = request.session.get('cart', {})
        quantity = cart.get(product)

        if quantity:
            if remove:
                if quantity <= 1:
                    cart.pop(product)
                else:
                    cart[product] = quantity - 1
            else:
                cart[product] = quantity + 1
        else:
            cart[product] = 1

        request.session['cart']  = cart
        request.session.modified = True
        return redirect('homepage')


class Cart(LoginRequiredMixin, View):
    login_url = '/store/login/'

    def get(self, request):
        cart = request.session.get('cart', {})
        ids = list(cart.keys())
        products = Product.get_products_by_id(ids)
        total = 0

        for product in products:
            quantity = cart.get(str(product.id), 1)
            product.cart_quantity = quantity
            product.total_price = product.price * quantity
            total += product.total_price

        return render(request, 'cart.html', {
            'products':products,
            'total':total,
        })


class CheckOut(LoginRequiredMixin, View):
    login_url = '/store/login/'

    def post(self, request):
        address = request.POST.get('address')
        phone  = request.POST.get('phone')
        cart = request.session.get('cart', {})

        customer, redir = get_or_redirect_customer(request)
        if redir:
            return redir

        if not cart:
            return redirect('cart')

        products = Product.get_products_by_id(list(cart.keys()))
        order = Order.objects.create(
            customer=customer,
            address=address,
            phone=phone,
        )
        for product in products:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart.get(str(product.id), 1),
                price=product.price,
            )

        request.session['cart']  = {}
        request.session.modified = True
        return redirect('orders')

class PaymentView(LoginRequiredMixin, View):
    login_url = '/store/login/'

    def get(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('homepage')

        products = Product.get_products_by_id(list(cart.keys()))
        total    = sum(
            product.price * cart.get(str(product.id), 1)
            for product in products
        )
        return render(request, 'payment.html', {
            'total':             total,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        })

    def post(self, request):
        cart = request.session.get('cart', {})

        if not cart:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        customer, redir = get_or_redirect_customer(request)
        if redir:
            return JsonResponse({'error': 'Profile not complete'}, status=400)

        products = Product.get_products_by_id(list(cart.keys()))
        total_paise = int(sum(
            product.price * cart.get(str(product.id), 1)
            for product in products
        ) * 100)

        if total_paise <= 0:
            return JsonResponse({'error': 'Invalid total amount'}, status=400)

        request.session['pending_address'] = request.POST.get('address', '').strip()
        request.session['pending_phone']   = request.POST.get('phone', '').strip()
        request.session.modified = True

        try:
            intent = stripe.PaymentIntent.create(
                amount = total_paise,
                currency = 'inr',
                metadata = {
                    'customer_id': customer.id,
                    'customer_name': str(customer),
                },
            )
            return JsonResponse({'client_secret': intent.client_secret})

        except stripe.error.CardError as e:
            return JsonResponse({'error': e.user_message}, status=400)

        except stripe.error.StripeError as e:
            return JsonResponse({'error': 'Payment service error. Please try again.'}, status=400)


class PaymentConfirm(LoginRequiredMixin, View):
    login_url = '/store/login/'

    def post(self, request):
        import json

        try:
            data = json.loads(request.body)
            payment_intent_id = data.get('payment_intent_id', '').strip()
            status = data.get('status', '').strip()
        except (json.JSONDecodeError, Exception):
            return JsonResponse({'error': 'Invalid request body'}, status=400)

        if not payment_intent_id:
            return JsonResponse({'error': 'Missing payment intent ID'}, status=400)

        customer, redir = get_or_redirect_customer(request)
        if redir:
            return JsonResponse({'error': 'Profile not complete'}, status=400)

        cart = request.session.get('cart', {})
        products = Product.get_products_by_id(list(cart.keys()))
        address = request.session.pop('pending_address', '')
        phone = request.session.pop('pending_phone', '')
        total = sum(
            product.price * cart.get(str(product.id), 1)
            for product in products
        )

        if status == 'succeeded':
            try:
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                if intent.status != 'succeeded':
                    raise ValueError('Payment not confirmed by Stripe')
            except stripe.error.StripeError:
                return JsonResponse({'error': 'Could not verify payment'}, status=400)

            order = Order.objects.create(
                customer = customer,
                address = address or 'Paid via Stripe',
                phone = phone or customer.phone,
                status = 'pending',
            )

            for product in products:
                OrderItem.objects.create(
                    order = order,
                    product = product,
                    quantity = cart.get(str(product.id), 1),
                    price = product.price,
                )

            PaymentModel.objects.create(
                order = order,
                customer = customer,
                stripe_id = payment_intent_id,
                amount = total,
                status = 'completed',
            )

            request.session['cart']  = {}
            request.session.modified = True

            return JsonResponse({
                'success': True,
                'redirect': '/store/orders/',
            })

        else:
            PaymentModel.objects.create(
                order  = None,
                customer = customer,
                stripe_id = payment_intent_id,
                amount = total,
                status = 'failed',
            )
            return JsonResponse({
                'success': False,
                'error': 'Payment was not completed. Please try again.',
            })
        

class OrderView(LoginRequiredMixin, View):
    login_url = '/store/login/'

    def get(self, request):
        customer, redir = get_or_redirect_customer(request)
        if redir:
            return redir

        orders = Order.objects.filter(
            customer=customer
        ).prefetch_related('items__product').order_by('-date')
        return render(request, 'orders.html', {'orders': orders})


class Login(View):
    def get(self, request):
        if request.user.is_authenticated:
            if not Customer.objects.filter(user=request.user).exists():
                return redirect('complete_profile')
            return redirect('homepage')
        return render(request, 'login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'Invalid email or password'})

        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            if not Customer.objects.filter(user=user).exists():
                return redirect('complete_profile')
            
            return_url = request.GET.get('next') or '/store/'
            return HttpResponseRedirect(return_url)

        return render(request, 'login.html', {'error': 'Invalid email or password'})

@login_required(login_url='/store/login/')
def logout(request):
    auth_logout(request)
    return redirect('login')


class Signup(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('homepage')
        return render(request, 'signup.html')

    def post(self, request):
        data = request.POST
        first_name = data.get('firstname')
        last_name = data.get('lastname')
        phone = data.get('phone')
        email = data.get('email')
        password = data.get('password')
        error = self.validate(first_name, last_name, phone, email, password)
        if error:
            return render(request, 'signup.html', {
                'error':  error,
                'values': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'email': email,
                }
            })

        user = User.objects.create_user(
            username  = email,
            email = email,
            password = password,
            first_name = first_name,
            last_name = last_name,
        )
        Customer.objects.create(user=user, phone=phone)
        auth_login(request, user)
        return redirect('homepage')

    def validate(self, first_name, last_name, phone, email, password):
        if not first_name or len(first_name) < 3:
            return 'First name must be at least 3 characters'
        if not last_name or len(last_name) < 3:
            return 'Last name must be at least 3 characters'
        if not phone or len(phone) < 10:
            return 'Phone number must be at least 10 digits'
        if not email or '@' not in email:
            return 'Enter a valid email address'
        if not password or len(password) < 5:
            return 'Password must be at least 5 characters'
        if User.objects.filter(email=email).exists():
            return 'Email already registered'
        return None


class CompleteProfile(LoginRequiredMixin, View):
    """
    Shown when a User exists but has no Customer profile.
    This handles edge cases like:
    - Admin-created users
    - Social auth users (future)
    - Any signup that failed mid-way
    """
    login_url = '/store/login/'

    def get(self, request):
        if Customer.objects.filter(user=request.user).exists():
            return redirect('homepage')
        return render(request, 'complete_profile.html', {
            'user': request.user
        })

    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        if not phone or len(phone) < 10:
            return render(request, 'complete_profile.html', {
                'error': 'Please enter a valid phone number (min 10 digits)',
                'user': request.user,
            })

        Customer.objects.create(
            user = request.user,
            phone = phone,
        )
        return redirect('homepage')