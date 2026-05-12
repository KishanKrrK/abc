"""
seed_categories.py — Run this once to populate the categories table.
Usage:  python seed_categories.py
"""
from app import app
from models import db, Category

CATEGORIES = [
    "Electronics",
    "Books & Stationery",
    "Clothing & Accessories",
    "Bags & Luggage",
    "Keys & Cards",
    "Sports Equipment",
    "Jewellery & Watches",
    "Documents & ID",
    "Water Bottles & Food",
    "Spectacles & Headphones",
    "Wallets & Money",
    "Other",
]

with app.app_context():
    for name in CATEGORIES:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.commit()
    print(f"Seeded {len(CATEGORIES)} categories successfully.")
