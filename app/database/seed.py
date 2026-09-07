"""
Database seeding — creates and populates sample e-commerce tables.

Tables:
- customers: id, name, email, city, country, created_at
- products: id, name, category, price, stock_quantity
- orders: id, customer_id, order_date, status, total_amount
- order_items: id, order_id, product_id, quantity, unit_price
"""

import random
from datetime import datetime, timedelta

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    MetaData,
    Table,
    inspect,
)

from app.database.connection import engine


metadata = MetaData()

# ── Table Definitions ───────────────────────────────────────────────────────

customers = Table(
    "customers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("email", String(150), nullable=False, unique=True),
    Column("city", String(100)),
    Column("country", String(100)),
    Column("created_at", DateTime, default=datetime.utcnow),
)

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(200), nullable=False),
    Column("category", String(100), nullable=False),
    Column("price", Float, nullable=False),
    Column("stock_quantity", Integer, default=0),
)

orders = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_id", Integer, ForeignKey("customers.id"), nullable=False),
    Column("order_date", DateTime, nullable=False),
    Column("status", String(50), nullable=False),
    Column("total_amount", Float, nullable=False),
)

order_items = Table(
    "order_items",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer, ForeignKey("orders.id"), nullable=False),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Float, nullable=False),
)


# ── Sample Data ─────────────────────────────────────────────────────────────

SAMPLE_CUSTOMERS = [
    ("Alice Johnson", "alice@example.com", "London", "UK"),
    ("Bob Smith", "bob@example.com", "New York", "USA"),
    ("Charlie Brown", "charlie@example.com", "Paris", "France"),
    ("Diana Prince", "diana@example.com", "Berlin", "Germany"),
    ("Ethan Hunt", "ethan@example.com", "Tokyo", "Japan"),
    ("Fiona Green", "fiona@example.com", "Sydney", "Australia"),
    ("George Miller", "george@example.com", "Toronto", "Canada"),
    ("Hannah Lee", "hannah@example.com", "Seoul", "South Korea"),
    ("Ivan Petrov", "ivan@example.com", "Moscow", "Russia"),
    ("Julia Roberts", "julia@example.com", "Los Angeles", "USA"),
    ("Kevin Hart", "kevin@example.com", "Chicago", "USA"),
    ("Laura Chen", "laura@example.com", "Shanghai", "China"),
    ("Marco Rossi", "marco@example.com", "Rome", "Italy"),
    ("Nina Patel", "nina@example.com", "Mumbai", "India"),
    ("Oscar Wild", "oscar@example.com", "Dublin", "Ireland"),
    ("Priya Sharma", "priya@example.com", "Delhi", "India"),
    ("Quinn Adams", "quinn@example.com", "Boston", "USA"),
    ("Raj Kapoor", "raj@example.com", "Bangalore", "India"),
    ("Sofia Garcia", "sofia@example.com", "Madrid", "Spain"),
    ("Tom Wilson", "tom@example.com", "Manchester", "UK"),
]

SAMPLE_PRODUCTS = [
    ("Laptop Pro 15", "Electronics", 1299.99, 45),
    ("Wireless Mouse", "Electronics", 29.99, 200),
    ("Mechanical Keyboard", "Electronics", 89.99, 150),
    ("USB-C Hub", "Electronics", 49.99, 100),
    ("Monitor 27 inch", "Electronics", 399.99, 60),
    ("Noise-Cancelling Headphones", "Electronics", 249.99, 80),
    ("Webcam HD", "Electronics", 79.99, 120),
    ("Standing Desk", "Furniture", 599.99, 30),
    ("Ergonomic Chair", "Furniture", 449.99, 25),
    ("Desk Lamp LED", "Furniture", 39.99, 180),
    ("Bookshelf Oak", "Furniture", 199.99, 40),
    ("Python Programming Book", "Books", 44.99, 300),
    ("Data Science Handbook", "Books", 39.99, 250),
    ("AI & Machine Learning Guide", "Books", 54.99, 200),
    ("Clean Code", "Books", 34.99, 350),
    ("Coffee Maker Deluxe", "Kitchen", 129.99, 70),
    ("Water Bottle Insulated", "Kitchen", 24.99, 500),
    ("Chef Knife Set", "Kitchen", 89.99, 90),
    ("Blender Pro", "Kitchen", 69.99, 110),
    ("Running Shoes", "Sports", 119.99, 160),
    ("Yoga Mat", "Sports", 29.99, 200),
    ("Fitness Tracker", "Sports", 149.99, 140),
    ("Dumbbells Set", "Sports", 79.99, 80),
    ("Backpack Travel", "Accessories", 69.99, 130),
    ("Sunglasses Polarized", "Accessories", 59.99, 170),
    ("Wallet Leather", "Accessories", 34.99, 220),
    ("Watch Smart", "Accessories", 199.99, 95),
    ("Phone Case Premium", "Accessories", 19.99, 400),
    ("Portable Charger", "Electronics", 39.99, 250),
    ("Desk Organizer", "Furniture", 29.99, 190),
]

ORDER_STATUSES = ["completed", "processing", "shipped", "delivered", "cancelled"]


def seed_database():
    """Create tables and insert sample data if tables don't already exist."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Only seed if tables don't exist yet
    if "customers" in existing_tables:
        print("📦 Database already seeded — skipping.")
        return

    print("🌱 Seeding database with sample e-commerce data...")

    # Create all tables
    metadata.create_all(engine)

    random.seed(42)  # Reproducible data

    with engine.begin() as conn:
        # Insert customers
        customer_data = [
            {
                "name": name,
                "email": email,
                "city": city,
                "country": country,
                "created_at": datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365)),
            }
            for name, email, city, country in SAMPLE_CUSTOMERS
        ]
        conn.execute(customers.insert(), customer_data)

        # Insert products
        product_data = [
            {
                "name": name,
                "category": category,
                "price": price,
                "stock_quantity": stock,
            }
            for name, category, price, stock in SAMPLE_PRODUCTS
        ]
        conn.execute(products.insert(), product_data)

        # Generate orders
        order_data = []
        all_order_items = []
        order_id = 1

        for _ in range(50):
            customer_id = random.randint(1, len(SAMPLE_CUSTOMERS))
            order_date = datetime(2024, 1, 1) + timedelta(
                days=random.randint(0, 500)
            )
            status = random.choice(ORDER_STATUSES)

            # Generate 1-4 items per order
            num_items = random.randint(1, 4)
            chosen_products = random.sample(
                range(1, len(SAMPLE_PRODUCTS) + 1), num_items
            )

            total_amount = 0.0
            for prod_id in chosen_products:
                quantity = random.randint(1, 5)
                unit_price = SAMPLE_PRODUCTS[prod_id - 1][2]
                total_amount += quantity * unit_price
                all_order_items.append(
                    {
                        "order_id": order_id,
                        "product_id": prod_id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                )

            order_data.append(
                {
                    "customer_id": customer_id,
                    "order_date": order_date,
                    "status": status,
                    "total_amount": round(total_amount, 2),
                }
            )
            order_id += 1

        conn.execute(orders.insert(), order_data)
        conn.execute(order_items.insert(), all_order_items)

    print(
        f"   ✅ Inserted {len(SAMPLE_CUSTOMERS)} customers, "
        f"{len(SAMPLE_PRODUCTS)} products, "
        f"{len(order_data)} orders, "
        f"{len(all_order_items)} order items."
    )
