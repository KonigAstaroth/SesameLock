from django.shortcuts import render
from django.http import HttpResponse
from firebase_admin import firestore

db = firestore.client()


# Create your views here.

def inicio(request):
    return render (request,'inicio.html')

def signup (request):
    return render (request, 'signup.html')

def login (request):
    return render (request, 'login.html')

def entradas (request):
    return render (request, 'entradas.html')

def salidas (request):
    return render (request, 'salidas.html')

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
            db.collection("Usuarios").add ({
            "name":name,
            "lastName": lastName,
            "email": email,
            "username": username,
            "password":password
        })
            return render (request, 'signupSuccess.html')  
        else :
                return HttpResponse("<h1> Datos faltantes </h1>")

    return HttpResponse("<h1> La contrasena no coincide </h1>")