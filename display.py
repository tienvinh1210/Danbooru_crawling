import requests
import json
import time
from pymongo import MongoClient, UpdateOne
from IPython.display import Image, display, HTML
import base64
import os

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'Danbooru' #Replace it with your own database name
COLLECTION_NAME = 'UmiTaki' #Replace it with your own collection name
if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI environment variable must be set with your MongoDB connection string."
    )

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
def displayall(collection:str, query):
    col = db[collection]
    l = list(col.find(query))
    html = """
    <html>
    <body>
    <div style="display:flex; flex-wrap:wrap;">
    """

    for post in l:
        try:
            r = requests.get(post['file_url'], timeout=30)
            r.raise_for_status()
            encoded = base64.b64encode(r.content).decode()
            html += f'<img src="data:image/jpeg;base64,{encoded}" style="height:150px; margin:5px;">'
        except:
            continue

    html += """
    </div>
    </body>
    </html>
    """
    with open("images.html", "w") as f:
        f.write(html)
#Sample query
displayall(COLLECTION_NAME,{'tag_string_general': 'holding_hands', 'rating':'g'})