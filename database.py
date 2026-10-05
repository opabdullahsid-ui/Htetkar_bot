# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, brand_id INTEGER,
        name TEXT NOT NULL, price_myr REAL NOT NULL, price_usdt REAL NOT NULL,
        specs_en TEXT NOT NULL, specs_my TEXT NOT NULL, image_url TEXT,
        FOREIGN KEY(brand_id) REFERENCES brands(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY, username TEXT)''')
    
    cursor.execute("INSERT OR IGNORE INTO brands (name) VALUES ('Apple'), ('Samsung'), ('Xiaomi')")
    
    # Defaults
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('start_msg', '<b>Welcome to H-Tech Digital Catalog!</b> ⚡\nPlease choose your language:')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('menu_msg_en', '⚡ <b>Welcome to H-Tech Digital Catalog</b> ⚡\n\nPlease choose an option below:')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('menu_msg_my', '⚡ <b>H-Tech Digital Catalog မှကြိုဆိုပါသည်</b> ⚡\n\nကျေးဇူးပြု၍ အောက်ပါရွေးချယ်မှုကို ရွေးချယ်ပါ:')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('menu_image', 'none')")
    
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def add_brand(name):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO brands (name) VALUES (?)", (name,))
        conn.commit()
        success = True
    except: success = False
    conn.close()
    return success

def get_brands():
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM brands")
    brands = cursor.fetchall()
    conn.close()
    return brands

def get_brand_name(brand_id):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM brands WHERE id=?", (brand_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "Unknown"

def get_setting(key):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "Welcome!"

def update_setting(key, value):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def add_product(brand_id, name, myr, usdt, specs_en, specs_my, image_url):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO products (brand_id, name, price_myr, price_usdt, specs_en, specs_my, image_url)
    VALUES (?, ?, ?, ?, ?, ?, ?)''', (brand_id, name, myr, usdt, specs_en, specs_my, image_url))
    conn.commit()
    conn.close()

def get_products_by_brand(brand_id):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products WHERE brand_id=?", (brand_id,))
    products = cursor.fetchall()
    conn.close()
    return products

def get_product_details(product_id):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.name, p.price_myr, p.price_usdt, p.specs_en, p.specs_my, p.image_url, b.name, p.brand_id
        FROM products p
        JOIN brands b ON p.brand_id = b.id
        WHERE p.id=?
    ''', (product_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def update_price(product_id, new_myr, new_usdt):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET price_myr=?, price_usdt=? WHERE id=?", (new_myr, new_usdt, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

def delete_brand(brand_id):
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE brand_id=?", (brand_id,))
    cursor.execute("DELETE FROM brands WHERE id=?", (brand_id,))
    conn.commit()
    conn.close()
