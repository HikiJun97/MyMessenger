from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')

# db.drop()
print(client.list_database_names())
db = client['test']
print(type(db))
db.dropDatabase()

