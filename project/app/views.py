from django.shortcuts import render


# Create your views here.

def inicio(request):
    return render(request,'inicio.html')

def signup (request):
    return render (request, 'signup.html')

def login (request):
    return render (request, 'login.html')