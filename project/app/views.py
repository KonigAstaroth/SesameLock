from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from firebase_admin import firestore, auth
import requests
from google.cloud.firestore_v1 import FieldFilter
from django.urls import reverse
import urllib.parse
from datetime import datetime, timedelta
import pytz
from collections import deque



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
        device = data.get("device_id")

    sesame_ref = db.collection("Sesame")
    sesame_query = sesame_ref.where(filter=FieldFilter("idLock", "==", device)).get()
    

    ultima_alerta = None
    if sesame_query:
        sesame_doc = sesame_query[0]
        sesame_data = sesame_doc.to_dict()
    
    
        if sesame_data.get("Alertas"):
            ultima_alerta = sesame_data["Alertas"][-1]  
        else:
            ultima_alerta = None
    else:
        sesame_query = None

    ultimo_acceso = None
    if sesame_query:
        sesame_doc = sesame_query[0]
        sesame_data = sesame_doc.to_dict()
    
    
        if sesame_data.get("Accesos"):
            ultimo_acceso = sesame_data["Accesos"][-1]  
        else:
            ultimo_acceso = None
    else:
        sesame_query = None
        

    invitado_a_eliminar = request.GET.get("eliminar", None)
    
    if invitado_a_eliminar and invitado_a_eliminar in Invitados:
        doc_ref.update({"Invitados": firestore.ArrayRemove([invitado_a_eliminar])})
        return redirect('/main')
         
    error_message = request.GET.get('error', None)
    success_message = request.GET.get("success", None)
                
    return render(request, 'inicio.html', {
         'error_message': error_message, 
         'success_message': success_message, 
         'name' : name, 
         "Invitados": Invitados, 
         "ultima_alerta": ultima_alerta,
         "ultimo_acceso": ultimo_acceso
         })

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

def estadisticas(request):
    session_cookie = request.COOKIES.get('sessionid')
    
    if not session_cookie:
        return redirect('/login')
    
    firebase_token = request.session.get("firebase_token")
    decoded_token = auth.verify_id_token(firebase_token)
    uid = decoded_token["uid"]
    
    return render(request, 'estadisticas.html')

def api_accesos_data(request):
    try:
        # Verificar autenticación
        firebase_token = request.session.get("firebase_token")
        if not firebase_token:
            return JsonResponse({"error": "No autorizado", "details": "Token no encontrado"}, status=401)
        
        try:
            decoded_token = auth.verify_id_token(firebase_token)
            uid = decoded_token["uid"]
        except Exception as e:
            return JsonResponse({"error": "Error de autenticación", "details": str(e)}, status=401)
        
        # Obtener el device_id del usuario
        user_doc = db.collection("Usuarios").document(uid).get()
        if not user_doc.exists:
            return JsonResponse({"error": "Usuario no encontrado"}, status=404)
        
        user_data = user_doc.to_dict()
        device_id = user_data.get("device_id")
        
        if not device_id:
            # Si no hay device_id, regresamos datos vacíos pero válidos
            empty_data = {
                "labels": ["1", "2", "3", "4", "5", "6", "7"],
                "counts": [0, 0, 0, 0, 0, 0, 0],
                "tooltips": [{"date": "Sin datos"} for _ in range(7)]
            }
            return JsonResponse(empty_data)
        
        # Obtener documento de Sesame con el device_id
        sesame_docs = db.collection("Sesame").where(filter=FieldFilter("idLock", "==", device_id)).get()
        
        if not sesame_docs:
            empty_data = {
                "labels": ["1", "2", "3", "4", "5", "6", "7"],
                "counts": [0, 0, 0, 0, 0, 0, 0],
                "tooltips": [{"date": "Sin datos"} for _ in range(7)]
            }
            return JsonResponse(empty_data)
        
        # Obtener todos los accesos
        sesame_data = sesame_docs[0].to_dict()
        accesos = sesame_data.get("Accesos", [])
        
        # Establecer zona horaria local (UTC-6 según los datos de ejemplo)
        timezone = pytz.timezone('America/Mexico_City')  # UTC-6
        
        # Obtener fecha actual en la zona horaria local
        now = datetime.now(timezone)
        
        # Crear un rango de 7 días hasta hoy
        date_range = []
        for i in range(6, -1, -1):
            date = now - timedelta(days=i)
            date_range.append(date)
        
        # Formatear labels para el eje X (día del mes) - CORREGIDO PARA COMPATIBILIDAD WINDOWS
        labels = []
        for date in date_range:
            # Usar %d y luego eliminar ceros a la izquierda manualmente
            day_str = date.strftime("%d").lstrip("0")
            if day_str == "":  # En caso de que el día sea "01" y termine como ""
                day_str = "1"
            labels.append(day_str)
        
        # Inicializar conteo de accesos por día
        daily_counts = [0] * 7
        
        # Crear información para tooltips
        tooltips = []
        for date in date_range:
            # Usar formato compatible con Windows
            month_names = {
                1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
                7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
            }
            
            day = date.strftime("%d").lstrip("0")
            if day == "": day = "1"
            month = month_names[date.month]
            year = date.strftime("%Y")
            
            tooltip_date = f"{day} de {month} de {year}"
            tooltips.append({
                "date": tooltip_date
            })
        
        # Contar accesos por día
        for acceso in accesos:
            try:
                # Si es un timestamp de Firestore
                if hasattr(acceso.get("timestamp"), "timestamp"):
                    acceso_date = acceso.get("timestamp").astimezone(timezone)
                else:
                    # Si es un string formateado como en el ejemplo
                    timestamp_str = acceso.get("timestamp")
                    if not timestamp_str:
                        continue
                        
                    # Ejemplo: "19 de marzo de 2025, 1:46:58 p.m. UTC-6"
                    # Primero intentar con el formato esperado
                    try:
                        timestamp_str = timestamp_str.replace("de ", "").replace(",", "").replace(".", "").replace("UTC-6", "")
                        acceso_date = datetime.strptime(timestamp_str, "%d %B %Y %I:%M:%S %p")
                        acceso_date = timezone.localize(acceso_date)
                    except ValueError:
                        # Si falla, intentar con otro formato posible
                        try:
                            # Para timestamps en formato estándar de Firestore
                            acceso_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            acceso_date = acceso_date.astimezone(timezone)
                        except ValueError:
                            # Si no podemos parsear el timestamp, ignoramos este acceso
                            print(f"No se pudo parsear el timestamp: {timestamp_str}")
                            continue
                
                # Verificar si el acceso está dentro del rango de 7 días
                for i, date in enumerate(date_range):
                    if (acceso_date.year == date.year and 
                        acceso_date.month == date.month and 
                        acceso_date.day == date.day):
                        daily_counts[i] += 1
                        break
            except Exception as e:
                # En caso de error al procesar la fecha, continúa con el siguiente acceso
                print(f"Error al procesar fecha: {e}")
                continue
        
        # Preparar datos para la respuesta
        data = {
            "labels": labels,
            "counts": daily_counts,
            "tooltips": tooltips
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        # Capturar cualquier excepción no manejada
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error no manejado: {e}\n{traceback_str}")
        return JsonResponse({"error": "Error interno del servidor", "details": str(e)}, status=500)

def api_dia_mas_accesos(request):
    try:
        # Verificar autenticación
        firebase_token = request.session.get("firebase_token")
        if not firebase_token:
            return JsonResponse({"error": "No autorizado", "details": "Token no encontrado"}, status=401)
        
        try:
            decoded_token = auth.verify_id_token(firebase_token)
            uid = decoded_token["uid"]
        except Exception as e:
            return JsonResponse({"error": "Error de autenticación", "details": str(e)}, status=401)
        
        # Obtener el device_id del usuario
        user_doc = db.collection("Usuarios").document(uid).get()
        if not user_doc.exists:
            return JsonResponse({"error": "Usuario no encontrado"}, status=404)
        
        user_data = user_doc.to_dict()
        device_id = user_data.get("device_id")
        
        if not device_id:
            # Si no hay device_id, regresamos datos vacíos pero válidos
            return JsonResponse({
                "day": "Sin datos",
                "date": "Sin datos",
                "count": 0
            })
        
        # Obtener documento de Sesame con el device_id
        sesame_docs = db.collection("Sesame").where(filter=FieldFilter("idLock", "==", device_id)).get()
        
        if not sesame_docs:
            return JsonResponse({
                "day": "Sin datos",
                "date": "Sin datos",
                "count": 0
            })
        
        # Obtener todos los accesos
        sesame_data = sesame_docs[0].to_dict()
        accesos = sesame_data.get("Accesos", [])
        
        if not accesos:
            return JsonResponse({
                "day": "Sin datos",
                "date": "Sin datos",
                "count": 0
            })
        
        # Establecer zona horaria local
        timezone = pytz.timezone('America/Mexico_City')  # UTC-6
        
        # Diccionario para contar accesos por día
        day_counts = {}
        
        # Procesar cada acceso y contar por día
        for acceso in accesos:
            try:
                # Si es un timestamp de Firestore
                if hasattr(acceso.get("timestamp"), "timestamp"):
                    acceso_date = acceso.get("timestamp").astimezone(timezone)
                    date_key = acceso_date.strftime("%Y-%m-%d")
                else:
                    # Si es un string formateado como en el ejemplo
                    timestamp_str = acceso.get("timestamp")
                    if not timestamp_str:
                        continue
                    
                    # Ejemplo: "19 de marzo de 2025, 1:46:58 p.m. UTC-6"
                    try:
                        timestamp_str = timestamp_str.replace("de ", "").replace(",", "").replace(".", "").replace("UTC-6", "")
                        acceso_date = datetime.strptime(timestamp_str, "%d %B %Y %I:%M:%S %p")
                        acceso_date = timezone.localize(acceso_date)
                        date_key = acceso_date.strftime("%Y-%m-%d")
                    except ValueError:
                        try:
                            # Para timestamps en formato estándar
                            acceso_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            acceso_date = acceso_date.astimezone(timezone)
                            date_key = acceso_date.strftime("%Y-%m-%d")
                        except ValueError:
                            print(f"No se pudo parsear el timestamp: {timestamp_str}")
                            continue
                
                # Incrementar contador para esta fecha
                if date_key in day_counts:
                    day_counts[date_key]["count"] += 1
                else:
                    # Formato para mostrar
                    month_names = {
                        1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
                        7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
                    }
                    
                    day_name = acceso_date.strftime("%A").capitalize()
                    # Traducir día de la semana al español si está en inglés
                    day_translations = {
                        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
                    }
                    day_name = day_translations.get(day_name, day_name)
                    
                    date_formatted = f"{acceso_date.day}/{acceso_date.month}/{acceso_date.year}"
                    
                    day_counts[date_key] = {
                        "date": date_formatted,
                        "day": day_name,
                        "count": 1,
                        "datetime": acceso_date  # Guardar para ordenar después
                    }
            
            except Exception as e:
                print(f"Error al procesar fecha de acceso: {e}")
                continue
        
        # Si no hay datos válidos después del procesamiento
        if not day_counts:
            return JsonResponse({
                "day": "Sin datos",
                "date": "Sin datos",
                "count": 0
            })
        
        # Encontrar el día con más accesos
        max_day = max(day_counts.values(), key=lambda x: x["count"])
        
        # Preparar respuesta
        result = {
            "day": max_day["day"],
            "date": max_day["date"],
            "count": max_day["count"]
        }
        
        return JsonResponse(result)
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error no manejado: {e}\n{traceback_str}")
        return JsonResponse({"error": "Error interno del servidor", "details": str(e)}, status=500)

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
     return render(request, 'aboutSesame.html')

    