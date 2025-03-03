import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("..\project\proyectosesamelock-firebase-adminsdk-fbsvc-588ce4654a.json")
firebase_admin.initialize_app(cred)

piña = 1;
