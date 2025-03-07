from django.shortcuts import render


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