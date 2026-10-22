import pytest
from app import app
from db import get_db_connection
from flask_jwt_extended import create_access_token
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test_secret123456789012345678901234'
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_clear_cart(client):
    access_token = create_access_token(identity="2") # user 2 (needs to be string)
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Add something to the cart to ensure it's not empty
    # first, create cart for user
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ensure cart exists
    cursor.execute("SELECT cart_id FROM carts WHERE user_id = %s", (2,))
    cart = cursor.fetchone()
    if not cart:
        cursor.execute("INSERT INTO carts (user_id) VALUES (%s)", (2,))
        conn.commit()
        cart_id = cursor.lastrowid
    else:
        cart_id = cart['cart_id']

    # insert into cart items
    try:
        cursor.execute("INSERT INTO cart_items (cart_id, variant_id, quantity) VALUES (%s, %s, %s)", (cart_id, 1, 2))
        conn.commit()
    except:
        pass

    # save inventory count
    cursor.execute("SELECT stock_quantity FROM inventory WHERE variant_id = 1")
    stock_before = cursor.fetchone()['stock_quantity']
    cursor.close()
    conn.close()

    # Clear cart
    rv = client.delete('/api/auth_cart/cart/clear', headers=headers)
    print("Response payload:", rv.data)
    assert rv.status_code == 200

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # check stock restored
    cursor.execute("SELECT stock_quantity FROM inventory WHERE variant_id = 1")
    stock_after = cursor.fetchone()['stock_quantity']
    assert stock_after == stock_before + 2

    # verify cart is empty
    cursor.execute("SELECT * FROM cart_items WHERE cart_id = %s", (cart_id,))
    items = cursor.fetchall()
    assert len(items) == 0

    # cleanup
    cursor.execute("DELETE FROM carts WHERE cart_id = %s", (cart_id,))
    conn.commit()
    cursor.close()
    conn.close()
