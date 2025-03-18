from django.shortcuts import render, redirect
from django.http import HttpResponse
from firebase_admin import firestore, auth
import requests


db = firestore.client()
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyAn4H4dq92zncCaIWowSs1qJk8WbUJkfqU"


# Create your views here.

def landing(request):
    return render (request,'landing.html')

def inicio(request):
    return render (request,'inicio.html')

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
                print(response.text)
                return redirect("inicio")
            else:
                return("<h1> Usuario o contrasena incorrectos </h1>")
        return render (request, 'login.html')

def entradas (request):
    return render (request, 'entradas.html')

def salidas (request):
    return render (request, 'salidas.html')

def estadisticas (request):
    return render (request, 'estadisticas.html')

def entradas_chart_view(request):
    # Datos hardcoded para probar
    dias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    conteos = [3, 6, 9, 8, 7, 4, 2]  # Valores que coinciden con tu gráfica original
    
    context = {
        'dias': dias,
        'conteos': conteos,
    }
    
    return render(request, 'estadisticas.html', context)

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
                return render (request, 'signupSuccess.html') 
            except Exception as e:
                    return HttpResponse(f"<h1>Error al registrar usuario: {str(e)}</h1>")
        else :
                return HttpResponse("<h1> Datos faltantes </h1>")

    return HttpResponse("<h1> La contrasena no coincide </h1>")

    