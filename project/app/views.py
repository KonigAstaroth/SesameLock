from django.shortcuts import render, redirect
from django.http import HttpResponse
from firebase_admin import firestore, auth
import requests
from google.cloud.firestore_v1 import FieldFilter
from django.urls import reverse
import urllib.parse





db = firestore.client()
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyAn4H4dq92zncCaIWowSs1qJk8WbUJkfqU"


# Create your views here.


def inicio(request):
    session_cookie = request.COOKIES.get('sessionid')
    
    if not session_cookie:
        return redirect('/login')
    
    firebase_token = request.session.get("firebase_token")
    decoded_token = auth.verify_id_token(firebase_token)
    uid = decoded_token["uid"]
    doc_ref = db.collection("Usuarios").document(uid)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        name = doc.to_dict().get("name")
        Invitados = data.get("Invitados", [])
        device = data.get("idLock")

    sesame_ref = db.collection("Sesame")
    query_ref = sesame_ref.where(filter=FieldFilter("idLock", "==", device)).get()

    if any(query_ref):
         alerts_ref = sesame_ref.get()
         datos = alerts_ref.to_dict()
         map_alerts = datos.get("Alertas", {})
        

    invitado_a_eliminar = request.GET.get("eliminar", None)
    
    if invitado_a_eliminar and invitado_a_eliminar in Invitados:
        doc_ref.update({"Invitados": firestore.ArrayRemove([invitado_a_eliminar])})
        return redirect('/main')
         
    error_message = request.GET.get('error', None)
    success_message = request.GET.get("success", None)
                
    return render(request, 'inicio.html', {'error_message': error_message, 'success_message': success_message, 'name' : name, "Invitados": Invitados})

def regInv(request):
    firebase_token = request.session.get("firebase_token")
    decoded_token = auth.verify_id_token(firebase_token)
    uid = decoded_token["uid"]
    doc_ref = db.collection("Usuarios").document(uid)
    guest_name = request.POST["guest_name"]
    doc_ref.update({"Invitados": firestore.ArrayUnion([guest_name])})
    success_message = "Invitado agregado"
    return redirect(f"/main?success={urllib.parse.quote(success_message)}")



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
            "device_id": device_id,
            "Permisos":True
        })
        for doc in query_ref:
            print(f"Documento encontrado con ID: {doc.id}")
            db.collection("Sesame").document(doc.id).update({
            "share_code": code
            })
        
        success_message = "Dispositivo registrado"
        return redirect(f"/main?success={urllib.parse.quote(success_message)}")
     else:
           print("there's nothing...")
           error_message = "No se encontró ningún dispositivo con ese ID"
           return redirect(f"/main?error={urllib.parse.quote(error_message)}")
     

def signup (request):
    error_message = request.GET.get('error', None)
    warning_message = request.GET.get('warning', None)
    return render (request, 'signup.html', {'error_message': error_message, 'warning_message': warning_message})
   

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
        if name and lastName and username and password:
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
                    error_message = e
                    return redirect(f"/signup?error={urllib.parse.quote(error_message)}")
        else :
                error_message = "Faltan campos por ser llenados"
                return redirect(f"/signup?error={urllib.parse.quote(error_message)}")

    warning_message = "No coinciden las contraseñas"
    return redirect(f"{reverse('signup')}?warning={urllib.parse.quote(warning_message)}")

def logout(request):
     request.session.flush()
     return redirect('login')

def aboutSesame(request):
     return render(request, 'aboutSesame')

    
