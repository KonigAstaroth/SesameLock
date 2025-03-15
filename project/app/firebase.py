import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("..\project\proyectosesamelock-firebase-adminsdk-fbsvc-588ce4654a.json")
app = firebase_admin.initialize_app(cred)


db = firestore.client()