import random
import decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Customer, Product, Order, OrderItem, Payment


class Command(BaseCommand):
    help = 'Seed database with 100 fake records'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding database...')
        self.create_categories()
        self.create_customers()
        self.create_products()
        self.create_orders()
        self.stdout.write(self.style.SUCCESS('✅ Done! 100 fake records created.'))

    def create_categories(self):
        categories = [
            'Electronics', 'Clothing', 'Books', 'Home & Kitchen',
            'Sports', 'Toys', 'Beauty', 'Automotive',
        ]
        for name in categories:
            Category.objects.get_or_create(name=name)
        self.stdout.write(f'  ✔ {len(categories)} categories created')

    def create_customers(self):
        first_names = ['Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun',
                       'Sai',   'Reyan',  'Ayaan',  'Krishna','Ishaan',
                       'Priya', 'Ananya', 'Isha',   'Riya',   'Kavya',
                       'Pooja', 'Neha',   'Sneha',  'Divya',  'Meera']

        last_names  = ['Patel', 'Shah', 'Modi', 'Desai', 'Mehta',
                       'Joshi', 'Rao',  'Nair', 'Iyer',  'Sharma']

        created = 0
        for i in range(20):
            first = random.choice(first_names)
            last  = random.choice(last_names)
            email = f'{first.lower()}.{last.lower()}{i}@example.com'

            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username   = email,
                    email      = email,
                    password   = 'Test@1234',
                    first_name = first,
                    last_name  = last,
                )
                Customer.objects.create(
                    user  = user,
                    phone = f'9{random.randint(100000000, 999999999)}',
                )
                created += 1

        self.stdout.write(f'  ✔ {created} customers created')

    def create_products(self):
        product_data = {
            'Electronics': [
                ('Samsung Galaxy S24',    45999.00),
                ('iPhone 15',             79999.00),
                ('OnePlus 12',            64999.00),
                ('Sony WH-1000XM5',       29999.00),
                ('Dell Inspiron Laptop',  55999.00),
                ('HP Pavilion',           49999.00),
                ('iPad Air',              59999.00),
                ('Smart Watch Pro',        8999.00),
                ('Bluetooth Speaker',      2999.00),
                ('USB-C Hub',              1999.00),
            ],
            'Clothing': [
                ('Cotton Kurta',           799.00),
                ('Denim Jeans',           1299.00),
                ('Formal Shirt',           999.00),
                ('Sports T-Shirt',         599.00),
                ('Winter Jacket',         2499.00),
                ('Saree Silk',            3999.00),
                ('Lehenga Choli',         5999.00),
                ('Casual Sneakers',       1799.00),
                ('Leather Belt',           499.00),
                ('Wool Sweater',          1499.00),
            ],
            'Books': [
                ('Python Crash Course',    499.00),
                ('Django for Beginners',   599.00),
                ('Clean Code',             699.00),
                ('The Pragmatic Programmer', 799.00),
                ('Rich Dad Poor Dad',      350.00),
                ('Atomic Habits',          399.00),
                ('Deep Work',             449.00),
                ('Ikigai',                299.00),
                ('Wings of Fire',         250.00),
                ('The Alchemist',         299.00),
            ],
            'Home & Kitchen': [
                ('Instant Pot',           4999.00),
                ('Air Fryer 5L',          3499.00),
                ('Mixer Grinder',         2299.00),
                ('Non-Stick Pan Set',     1299.00),
                ('Water Purifier',        8999.00),
                ('Electric Kettle',        799.00),
                ('Microwave Oven',        7999.00),
                ('Rice Cooker',           1999.00),
                ('Bed Sheet Set',          999.00),
                ('Cushion Cover Pack',     499.00),
            ],
            'Sports': [
                ('Cricket Bat',           1999.00),
                ('Football',               799.00),
                ('Yoga Mat',               599.00),
                ('Dumbbells 5kg Pair',    1299.00),
                ('Badminton Racket Set',   999.00),
                ('Cycling Helmet',        1499.00),
                ('Swimming Goggles',       499.00),
                ('Running Shoes',         2999.00),
                ('Jump Rope',              299.00),
                ('Resistance Bands Set',   599.00),
            ],
            'Toys': [
                ('LEGO City Set',         2999.00),
                ('Remote Control Car',    1499.00),
                ('Barbie Doll',            799.00),
                ('Board Game Monopoly',    999.00),
                ('Puzzle 1000 Pieces',     599.00),
                ('Hot Wheels Track',      1299.00),
                ('Rubik\'s Cube',          299.00),
                ('Action Figure Set',      699.00),
                ('Play-Doh Kit',           499.00),
                ('Wooden Blocks',          399.00),
            ],
            'Beauty': [
                ('Face Wash',              299.00),
                ('Moisturizer SPF 50',     599.00),
                ('Lipstick Set',           799.00),
                ('Hair Dryer',            1999.00),
                ('Perfume 100ml',         1299.00),
                ('Sunscreen Lotion',       399.00),
                ('Eye Shadow Palette',     699.00),
                ('Beard Trimmer',         1499.00),
                ('Shampoo & Conditioner',  499.00),
                ('Nail Polish Set',        349.00),
            ],
            'Automotive': [
                ('Car Dash Cam',          3999.00),
                ('Tyre Inflator',         1999.00),
                ('Car Vacuum Cleaner',    1499.00),
                ('Seat Cover Set',        2499.00),
                ('Car Phone Mount',        499.00),
                ('Jump Starter Pack',     4999.00),
                ('Steering Wheel Cover',   599.00),
                ('Car Air Freshener',      199.00),
                ('OBD2 Scanner',          2999.00),
                ('Parking Sensor Kit',    1999.00),
            ],
        }

        created = 0
        for category_name, products in product_data.items():
            category = Category.objects.get(name=category_name)
            for name, price in products:
                Product.objects.get_or_create(
                    name     = name,
                    defaults = {
                        'price':       decimal.Decimal(str(price)),
                        'category':    category,
                        'description': f'{name} — high quality product in {category_name}.',
                        'image':       'uploads/products/default.jpg',
                    }
                )
                created += 1

        self.stdout.write(f'  ✔ {created} products created')

    def create_orders(self):
        customers = list(Customer.objects.all())
        products  = list(Product.objects.all())

        STATUS_CHOICES  = ['pending', 'shipped', 'delivered', 'cancelled']
        PAYMENT_CHOICES = ['pending', 'completed', 'failed']

        orders_created  = 0
        payment_created = 0

        for _ in range(50):
            customer      = random.choice(customers)
            num_items     = random.randint(1, 5)
            order_products = random.sample(products, num_items)
            order_status  = random.choice(STATUS_CHOICES)

            order = Order.objects.create(
                customer = customer,
                address  = f'{random.randint(1,999)}, Sample Street, Rajkot, Gujarat',
                phone    = customer.phone,
                status   = order_status,
            )

            order_total = decimal.Decimal('0.00')
            for product in order_products:
                qty   = random.randint(1, 4)
                price = product.price
                OrderItem.objects.create(
                    order    = order,
                    product  = product,
                    quantity = qty,
                    price    = price,
                )
                order_total += price * qty

            if order_status == 'cancelled':
                pay_status = 'failed'
            elif order_status == 'delivered':
                pay_status = 'completed'
            else:
                pay_status = random.choice(PAYMENT_CHOICES)

            Payment.objects.create(
                order     = order,
                customer  = customer,
                stripe_id = f'pi_test_{random.randint(100000000, 999999999)}',
                amount    = order_total,
                status    = pay_status,
            )

            orders_created  += 1
            payment_created += 1

        self.stdout.write(f'  ✔ {orders_created} orders created')
        self.stdout.write(f'  ✔ {payment_created} payments created')
