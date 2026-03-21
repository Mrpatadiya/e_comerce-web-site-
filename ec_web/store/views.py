from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from store.models import Product, Order, OrderItem, Customer, Category


class LoginRequired:
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('customer'):
            return redirect(f'/store/login/?return_url={request.path}')
        return super().dispatch(request, *args, **kwargs)


class Index(View):
    def get(self, request):
        return HttpResponseRedirect(f'/store{request.get_full_path()[1:]}')

    def post(self, request):
        product= request.POST.get('product')
        remove= request.POST.get('remove')
        cart= request.session.get('cart', {})
        quantity= cart.get(product)

        if quantity:
            if remove:
                cart[product]= quantity -1 if quantity >1 else cart.pop(product) or 0
            else:
                cart[product]= quantity +1
        else:
            cart[product]= 1

        request.session['cart']= cart
        return redirect('homepage')

    def store(request):
        if not request.session.get('cart'):
            request.session['cart']= {}

        categories= Category.get_all_categories()
        category_id= request.GET.get('category')
        products= Product.get_all_products_by_categoryid(category_id) if category_id else Product.get_all_products()

        return render(request, 'index.html',{
            'products':products,
            'categories':categories,
        })


class Cart(LoginRequired, View):
    def get(self, request):
        cart= request.session.get('cart', {})
        ids= list(cart.keys())
        products= Product.get_products_by_id(ids)
        for product in products:
            product.cart_quantity= cart.get(str(product.id),1)
        return render(request, 'cart.html', {'products': products})

class CheckOut(LoginRequired, View):
    def post(self, request):
        address= request.POST.get('address')
        phone= request.POST.get('phone')
        customer_id= request.session.get('customer')
        cart= request.session.get('cart', {})

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return redirect('login')

        products= Product.get_products_by_id(list(cart.keys()))

        order= Order.objects.create(
            customer=customer,
            address=address,
            phone=phone,
        )
        for product in products:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart.get(str(product.id),1),
                price=product.price,
            )

        request.session['cart']= {}
        return redirect('orders')

class OrderView(LoginRequired, View):
    def get(self, request):
        customer_id= request.session.get('customer')
        orders= Order.objects.filter(
            customer_id=customer_id
        ).prefetch_related('items__product').order_by('-date')
        return render(request, 'orders.html', {'orders': orders})

class Login(View):
    def get(self, request):
        request.session['return_url']= request.GET.get('return_url')
        return render(request, 'login.html')

    def post(self, request):
        email= request.POST.get('email')
        password= request.POST.get('password')

        try:
            user= User.objects.get(email=email)
            user= authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user= None

        if user:
            auth_login(request, user)
            customer= Customer.objects.get(user=user)
            request.session['customer'] = customer.id
            return_url= request.session.pop('return_url', None)
            return HttpResponseRedirect(return_url or '/store/')

        return render(request, 'login.html', {'error': 'Invalid email or password'})

def logout(request):
    auth_logout(request)
    request.session.clear()   
    return redirect('login')


class Signup(View):
    def get(self, request):
        return render(request, 'signup.html')

    def post(self, request):
        data= request.POST
        first_name= data.get('firstname')
        last_name= data.get('lastname')
        phone= data.get('phone')
        email= data.get('email')
        password= data.get('password')

        error= self.validate(first_name, last_name, phone, email, password)
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
            username=email,       
            email=email,
            password=password, 
            first_name=first_name,
            last_name=last_name,
        )
        Customer.objects.create(user=user, phone=phone)

        return redirect('login')  

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