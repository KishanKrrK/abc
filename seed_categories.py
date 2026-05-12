from app import app, mongo

CATEGORIES = [
    'Electronics', 'Books & Stationery', 'Clothing & Accessories',
    'ID Cards & Documents', 'Keys', 'Bags & Wallets',
    'Sports Equipment', 'Jewellery', 'Other'
]

with app.app_context():
    for name in CATEGORIES:
        if not mongo.db.categories.find_one({'name': name}):
            mongo.db.categories.insert_one({'name': name})
            print(f"Inserted category: {name}")
        else:
            print(f"Category already exists: {name}")
    print("Done seeding categories.")
