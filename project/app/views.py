from django.shortcuts import render, redirect
from django.http import HttpResponse
from firebase_admin import firestore, auth
import requests
from google.cloud.firestore_v1 import FieldFilter
from django.urls import reverse
import firebase_admin




db = firestore.client()
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyAn4H4dq92zncCaIWowSs1qJk8WbUJkfqU"


# Create your views here.


def inicio(request):
    session_cookie = request.COOKIES.get('sessionid')
    
    if not session_cookie:
        return redirect('/login')
    
    error_message = request.GET.get('error', None)
                
    return render(request, 'inicio.html', {'error_message': error_message})

def regDev(request):
     firebase_token = request.session.get("firebase_token")
     decoded_token = auth.verify_id_token(firebase_token)
     uid = decoded_token["uid"]
     device_id = request.POST["device_id"]
     code = request.POST["share_code"]

     print(device_id)
     print(type(device_id))

     sesame_ref = db.collection("Sesame")
     query_ref = sesame_ref.where(filter=FieldFilter("idLock", "==", device_id)).get()
     
     if any(query_ref):
        print("Hay elementos!!!!")
        
        db.collection("Usuarios").document(uid).update ({
            "device_id": device_id
        })
        for doc in query_ref:
            print(f"Documento encontrado con ID: {doc.id}")
            db.collection("Sesame").document(doc.id).update({
            "share_code": code
            })
        
        return redirect("inicio")
     else:
           print("there's nothing...")
           url = reverse('inicio') + '?error=dispositivo_no_encontrado'
           return redirect(url)
     

def signup (request):
    
    return render (request, 'signup.html')
   

def login (request):
        if request.method == "POST":
            email = request.POST["email"]
            password = request.POST["password"]

            data = {"email": email, "password": password, "returnSecureToken": True}
            response = requests.post(FIREBASE_AUTH_URL, json=data)

            if response.status_code == 200:
                user_data = response.json()
                request.session["firebase_uid"] = user_data["localId"]
                request.session["email"] = email
                request.session["firebase_token"] = user_data["idToken"]
                
                return redirect("inicio")
               
            else:
                return render (request, 'login.html')
        return render (request, 'login.html')


def estadisticas (request):
    return render (request, 'estadisticas.html')

def add(request):
    name = request.POST["name"]
    lastName = request.POST["lastName"]
    email = request.POST["email"]
    username = request.POST["username"]
    password = request.POST["password"]
    confirmPassword = request.POST["confirmPassword"]

    if password == confirmPassword:
        if '@' in email and name and lastName and username and password:
            try:
                user = auth.create_user(email=email, password=password)
                db.collection("Usuarios").document(user.uid).set ({
                "name":name,
                "lastName": lastName,
                "email": email,
                "username": username,
                
        })
                return redirect('login')
            except Exception as e:
                    return HttpResponse(f"<h1>Error al registrar usuario: {str(e)}</h1>")
        else :
                return HttpResponse("<h1> Datos faltantes </h1>")

    return HttpResponse("<h1> La contrasena no coincide </h1>")

def logout(request):
     request.session.flush()
     return redirect('login')

def aboutSesame(request):
     return render(request, 'aboutSesame')

    