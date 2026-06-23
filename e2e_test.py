import urllib.request
import urllib.parse
from http.cookiejar import CookieJar
import json

# Setup cookie jar to act like a real browser session
cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

BASE_URL = "http://127.0.0.1:5000"

print("--- STARTING END-TO-END USER POV TEST ---")

# 1. Register a new SaaS user & restaurant
print("\n[1] Registering a new Restaurant: 'Test Diner'...")
register_data = urllib.parse.urlencode({
    'name': 'Test User',
    'restaurant_name': 'Test Diner',
    'email': 'test@diner.com',
    'password': 'password123'
}).encode('utf-8')
req = urllib.request.Request(f"{BASE_URL}/register", data=register_data, method='POST')
res = urllib.request.urlopen(req)
print(f"Registered! Redirected to: {res.url}")

# 2. Go to the Menu Admin page and add a Menu Item
print("\n[2] Owner adds a new Menu Item via Dashboard...")
menu_data = urllib.parse.urlencode({
    'name': 'Super Mega Burger',
    'price': '15.99',
    'description': 'The biggest burger in town.',
    'image_url': ''
}).encode('utf-8')
req = urllib.request.Request(f"{BASE_URL}/menu", data=menu_data, method='POST')
res = urllib.request.urlopen(req)
print(f"Menu item added! Redirected to: {res.url}")

# 3. Simulate a CUSTOMER visiting the custom storefront
print("\n[3] Customer visits the custom storefront (test-diner.127.0.0.1:5000)...")
# We need to fetch the item ID that was just created.
# Easiest way in this test is to hit the storefront and parse the HTML.
storefront_url = "http://127.0.0.1:5000"
req = urllib.request.Request(storefront_url, headers={'Host': 'test-diner.127.0.0.1:5000'})
res = urllib.request.urlopen(req)
html = res.read().decode('utf-8')

if "Super Mega Burger" in html:
    print("SUCCESS: Storefront loaded correctly and displays the 'Super Mega Burger'.")
else:
    print("ERROR: Storefront did not load the item.")

# Extract the item ID from the HTML (looking for /cart/add/X)
import re
match = re.search(r'/cart/add/(\d+)', html)
item_id = match.group(1) if match else "1"
print(f"Found Item ID: {item_id}")

# 4. Customer adds item to cart
print("\n[4] Customer adds the burger to the cart...")
# Note: Since the customer is on the subdomain, we must pass the Host header and use a NEW cookie jar
# because cookies are bound to the domain.
customer_cookie_jar = CookieJar()
customer_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(customer_cookie_jar))

req = urllib.request.Request(
    f"{BASE_URL}/cart/add/{item_id}", 
    data=b"", # Empty POST
    headers={'Host': 'test-diner.127.0.0.1:5000'}
)
res = customer_opener.open(req)
print("Item added to cart successfully.")

# 5. Customer views cart
print("\n[5] Customer views the cart...")
req = urllib.request.Request(
    f"{BASE_URL}/cart", 
    headers={'Host': 'test-diner.127.0.0.1:5000'}
)
res = customer_opener.open(req)
cart_html = res.read().decode('utf-8')

if "Quantity: 1" in cart_html and "15.99" in cart_html:
    print("SUCCESS: Cart displays the correct quantity and total price ($15.99).")
else:
    print("ERROR: Cart did not calculate correctly.")

# 6. Customer checks out
print("\n[6] Customer proceeds to checkout...")
checkout_data = urllib.parse.urlencode({
    'customer_name': 'Alice Wonder'
}).encode('utf-8')
req = urllib.request.Request(
    f"{BASE_URL}/checkout", 
    data=checkout_data,
    headers={'Host': 'test-diner.127.0.0.1:5000'}
)
res = customer_opener.open(req)
success_html = res.read().decode('utf-8')
if "Order Placed Successfully" in success_html and "Alice Wonder" in success_html:
    print("SUCCESS: Order was placed successfully!")
else:
    print("ERROR: Order placement failed.")

# 7. Owner checks orders dashboard
print("\n[7] Owner views incoming orders...")
req = urllib.request.Request(f"{BASE_URL}/orders")
res = urllib.request.urlopen(req) # using the OWNER's cookie jar
orders_html = res.read().decode('utf-8')
if "Alice Wonder" in orders_html and "1x Super Mega Burger" in orders_html and "15.99" in orders_html:
    print("SUCCESS: The order appeared on the owner's dashboard!")
else:
    print("ERROR: Order did not appear on the dashboard.")

print("\n--- ALL TESTS PASSED! ---")
