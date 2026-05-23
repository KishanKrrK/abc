from pymongo import MongoClient

MONGO_URI = "mongodb+srv://kishan9798760468_db_user:joGeYTKH1bfd9neF@cluster0.nro9z2t.mongodb.net/lost_found_db?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['lost_found_db']

# Fix LOST -> lost
r1 = db.items.update_many({'status': 'LOST'}, {'$set': {'status': 'lost'}})
# Fix FOUND -> found
r2 = db.items.update_many({'status': 'FOUND'}, {'$set': {'status': 'found'}})

print("LOST fixed:", r1.modified_count)
print("FOUND fixed:", r2.modified_count)
print("lost in DB:", db.items.count_documents({'status': 'lost'}))
print("found in DB:", db.items.count_documents({'status': 'found'}))
client.close()
