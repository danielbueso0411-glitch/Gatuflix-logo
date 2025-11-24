import time
import re
import os
import logging
import telebot
import threading
import urllib.parse
import psutil
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# --- LIBRERÍAS SELENIUM ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont

# --- 1. AUTO-CONFIGURACIÓN INICIAL (DESCARGA DE RECURSOS) ---
# Como Railway no tiene "Celda 1", el bot descarga sus propias imágenes al arrancar.
print("🔧 Verificando recursos visuales...")

RECURSOS = {
    "/content/gatuflix_logo_normal.png": "https://raw.githubusercontent.com/danielbueso0411-glitch/Gatuflix-logo/65dd9a9901297dd64d1c8b644be4a91b9ad55263/Gatuflix%20logo.png",
    "/content/gatuflix_logo_triste.png": "https://raw.githubusercontent.com/danielbueso0411-glitch/Gatuflix-logo/ec3890ae1b3b654f953943e0f03e6b91405ea7cb/No_se_encontro.png",
    "/content/tutorial_paso_1.png": "https://raw.githubusercontent.com/danielbueso0411-glitch/Gatuflix-logo/main/TV_HOGAR.png",
    "/content/tutorial_paso_2.png": "https://raw.githubusercontent.com/danielbueso0411-glitch/Gatuflix-logo/main/Enviar_email.png"
}

# Crear carpeta /content si no existe (por seguridad)
if not os.path.exists("/content"):
    os.makedirs("/content")

for ruta, url in RECURSOS.items():
    if not os.path.exists(ruta):
        print(f"⬇️ Descargando: {ruta}...")
        os.system(f"wget -q -O {ruta} \"{url}\"")
    else:
        print(f"✅ Recurso listo: {ruta}")

# --- 2. CONFIGURACIÓN DEL SISTEMA ---
# Silenciar logs innecesarios
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Credenciales de Google Sheets (Incrustadas para facilitar el deploy)
CREDENCIALES_JSON = {
  "type": "service_account",
  "project_id": "rich-karma-478818-h4",
  "private_key_id": "064598e0dcfd72cf42676690943985c71e513f8d",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDwLoDrHLlqg8FV\nMGQpudwyXE73z/i+F55E9vlT1+EBYVyprdAtllPLmjsImW6HkCbZxNduo67Z21M0\nEQw327i09GpB97sW51/uT7Z17VgGVaN7y5mptYq0V/bFFxvw/ZmcvJT3a6ALa5mH\nVIfQG5G/yx9HVeWTYMNqLdsGXwz0WjadDmhUBGKxltCB+Pmz3vZ7w0cKM10D5P7Q\n5NERplKxy03BdgbA+57kvjTBNvWMXcj453u0ka6E/4u49FLxt3D13tYY9vdJaHhI\nJIPutA7BZprpEQaloR6vrSH7HR7tMZ0PSShpnkS1ak3qq28EAUf1SFkmTZZ3aZSG\nh93epLyLAgMBAAECggEALvOwUQXa+0cJZslgc0W5lYC1ET2vLx332xx6rhjADCCH\n2EW5sge2ltEuJCa2VDrqVVzlDmRiHIWDFOUWQd8qkvlKwl2WzcnqV3Bux0vgDtDz\n9hHdlq7+D/Y4L9wuIqS4wEqfRmTcMw9UQn/UUuroyZkAItZYXECowtt2+x5erm+J\nVWCqlx+5ZCq17N7szGwDFmvDwfqCfyfzehIW2tRXq/J3ToXK1yuXWhgvDHUu6R3k\nBOvrJgZbKfVTbCprkq+b6N2oMCGjcnIvJd/2n2yEUMLYq7Gt7ms6EzNVLVk28Nwx\nJtllfXEavth/TpO3dlrDjSYkLXUY1EwMn6GOYZuCOQKBgQD5fFKvP7jVt9HDj5j3\nBIPKWRb4uLuDyMa5OFdOKkQSU73Cntf868+kM43098hWAwyEd9juWSuoFfZv3NN6\nYGO5J5na2ReqLHZKHuPdu/z6tWXvGo4Vqe2AEYeEUZ0v/N6/T9ClkKHQCeax7xhZ\n+IXfRAbCXWmETvEA+9AdKbedswKBgQD2c/0ODp+5ia2rc+bTc1Lo3gH5swuObMEz\n693ZxHYS165N0g7HpJY5Lqo/J5Kp11TSWbajxyvu/Q7lYQWlSBljc7gv1iQHJO0c\n7Ood8+imI9uiwQbPc40BIXX3U/LiYOjuX0a1hnp4Agqf/NU7Y5QRlRj/un0EjWw4\nEghZoEbpyQKBgAJA7T5IBRNpJavukCMrF0WsqFh20rrOBX2G1MMP/q1rtDsd1DWk\nq6uAC7g6xMSCIorPylXc2FgcWq2IASEJ3dy+TtV7QIt4+1iQDt7h49cf7FvMkZwA\nfPS7M84uLo1Qa3Ku9eOI+u02Ka9RyZaGeC8cHjODRIC9dc/cdnTM+6uhAoGAEgcm\nCbM0J+RUWeheiDU1aWdkCZn5TG/UKjIkxltCr9orG/IztpLpkkFBnuEML3Ra9hAt\n9gkJw6+rOUhBm3eMs+OxI36soAEpfyYtcgd3iz+wP1WTY/V16RFDidYQPFMOdvFt\nQLYXm1O65z0dc/yyxh5796jyoDSgJ/HZvoSk61ECgYEAlzbxH+aLH5A68S7wvrEp\ngQ77M2bQbrgqaXPznRKBTvDJHilvmUTUvpaFFWTMltzn2jnRvqJBHigFEyN9lJGI\n9yzWlh0ZvQCKBBpGl22DijuK5+QeXaQvutUcbFXvk8L3NQ/JjSMIWm/PYys0KvcF\nvE3+wJfuItlG0EHfobobob5YA=\n-----END PRIVATE KEY-----\n",
  "client_email": "bot-excel@rich-karma-478818-h4.iam.gserviceaccount.com",
  "client_id": "102906888729312345516",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/bot-excel%40rich-karma-478818-h4.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# --- DATOS DEL BOT ---
TOKEN = "8033181105:AAG9XLXvaim4uiwhWCO8dsyAzHdPjCwbz_U"
ADMIN_IDS = {1628575356, 1730837543}
LIMITE_DIARIO = 3
NOMBRE_HOJA_EXCEL = "Gatuflix_Logs"
NUMERO_SOPORTE = "50493293658"

# --- CIRCUIT BREAKER ---
CB_UMBRAL_FALLOS = 10
CB_VENTANA_TIEMPO = 300
historial_fallos_global = []
MODO_MANTENIMIENTO = False

USUARIOS_AUTORIZADOS = set(ADMIN_IDS)
TODOS_LOS_USUARIOS = set(ADMIN_IDS)

bot = telebot.TeleBot(TOKEN)
estado_tareas = {}
candado_bot = threading.Lock()
contadores_retry = {}
uso_diario = {}
historial_usuarios = {}
cola_global = []

bot.set_my_commands([
    BotCommand("codigo", "Solicitar código"),
    BotCommand("historial", "Ver mis últimos códigos"),
    BotCommand("start", "Instrucciones")
])

# --- FUNCIONES AUXILIARES ---
def traducir_error_amigable(excepcion):
    error_str = str(excepcion).lower()
    if "no hay mensajes" in error_str: return "📭 <b>Bandeja Vacía.</b>\nLa cuenta no tiene correos de Netflix recientes."
    if "timeout" in error_str: return "⏳ <b>Tiempo agotado.</b>\nLa página no respondió a tiempo."
    return f"⚠️ <b>Error técnico:</b> {str(excepcion)[:30]}"

def registrar_fallo_sistema():
    global MODO_MANTENIMIENTO, historial_fallos_global
    if MODO_MANTENIMIENTO: return
    ahora = time.time()
    historial_fallos_global.append(ahora)
    historial_fallos_global = [t for t in historial_fallos_global if ahora - t < CB_VENTANA_TIEMPO]
    if len(historial_fallos_global) >= CB_UMBRAL_FALLOS:
        MODO_MANTENIMIENTO = True
        historial_fallos_global = []
        notificar_admins(f"🚨 <b>ALERTA CRÍTICA</b>\nBot en MODO MANTENIMIENTO.")
        global cola_global
        cola_global = []

def registrar_en_sheets(chat_id, correo, estado, detalle):
    def _tarea_fondo():
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENCIALES_JSON, scope)
            client = gspread.authorize(creds)
            sheet = client.open(NOMBRE_HOJA_EXCEL).sheet1
            fecha = datetime.now().strftime("%Y-%m-%d")
            hora = datetime.now().strftime("%H:%M:%S")
            fila = [fecha, hora, str(chat_id), correo, estado, detalle]
            sheet.append_row(fila)
        except: pass
    threading.Thread(target=_tarea_fondo).start()

def es_admin(id_usuario): return id_usuario in ADMIN_IDS
def es_autorizado(id_usuario):
    if es_admin(id_usuario): return True
    return id_usuario in USUARIOS_AUTORIZADOS
def registrar_usuario(chat_id): TODOS_LOS_USUARIOS.add(chat_id)

def verificar_limite(chat_id):
    if es_admin(chat_id): return True, 0
    hoy = str(date.today())
    if chat_id not in uso_diario or uso_diario[chat_id]['fecha'] != hoy:
        uso_diario[chat_id] = {'fecha': hoy, 'conteo': 0}
    conteo = uso_diario[chat_id]['conteo']
    return conteo < LIMITE_DIARIO, conteo

def incrementar_uso(chat_id):
    if es_admin(chat_id): return
    hoy = str(date.today())
    if chat_id in uso_diario and uso_diario[chat_id]['fecha'] == hoy:
        uso_diario[chat_id]['conteo'] += 1

def denegar_acceso(chat_id):
    markup = InlineKeyboardMarkup()
    url = f"https://wa.me/{NUMERO_SOPORTE}?text={urllib.parse.quote(f'Hola, solicito acceso. ID: {chat_id}')}"
    markup.add(InlineKeyboardButton("🔐 Solicitar Acceso", url=url))
    bot.send_message(chat_id, f"🔒 <b>ACCESO DENEGADO</b>", parse_mode="HTML", reply_markup=markup)

def notificar_admins(mensaje):
    for admin_id in ADMIN_IDS:
        try: bot.send_message(admin_id, mensaje, parse_mode="HTML")
        except: pass

def guardar_historial(chat_id, correo, codigo):
    if chat_id not in historial_usuarios: historial_usuarios[chat_id] = []
    entrada = {"fecha": datetime.now().strftime("%d/%m %H:%M"), "correo": correo, "codigo": codigo}
    historial_usuarios[chat_id].append(entrada)
    if len(historial_usuarios[chat_id]) > 3: historial_usuarios[chat_id].pop(0)

def actualizar_mensajes_cola():
    for index, usuario in enumerate(cola_global):
        pos = index + 1
        txt = (f"⏳ <b>En Fila (#{pos})</b>\n📧 <code>{usuario['email']}</code>")
        try: bot.edit_message_text(txt, usuario['chat_id'], usuario['msg_id'], parse_mode="HTML", reply_markup=teclado_cancelar())
        except: pass

def remover_de_cola(chat_id):
    global cola_global
    cola_global = [u for u in cola_global if u['chat_id'] != chat_id]
    actualizar_mensajes_cola()

# --- COMANDOS ADMIN ---
@bot.message_handler(commands=['status'])
def admin_status(m):
    if not es_admin(m.chat.id): return
    bot.reply_to(m, "📊 **Status OK** (Railway)", parse_mode="Markdown")

@bot.message_handler(commands=['reiniciar'])
def admin_reiniciar(m):
    if not es_admin(m.chat.id): return
    os.system("pkill chrome")
    bot.reply_to(m, "✅ Procesos limpiados.")

# --- FUNCIONES GRÁFICAS ---
def generar_logo_texto_cabecera():
    img = Image.new('RGBA', (400, 100), color=(255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    try: fnt = ImageFont.truetype("arial.ttf", 70)
    except: fnt = ImageFont.load_default()
    d.text((10, 10), "GATUFLIX", font=fnt, fill=(0,0,0))
    return img

def editar_captura_con_gatuflix(ruta_original, tipo_error="generico"):
    try:
        img_original = Image.open(ruta_original).convert("RGBA")
        ancho_total, alto_total = img_original.size
        centro_x = ancho_total // 2
        try: logo_cabecera = Image.open('/content/gatuflix_logo_normal.png').convert("RGBA")
        except: logo_cabecera = generar_logo_texto_cabecera()

        target_h_cab = 120
        new_w_cab = int(target_h_cab * (logo_cabecera.width / logo_cabecera.height))
        logo_cabecera = logo_cabecera.resize((new_w_cab, target_h_cab), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img_original)
        bg_color_web = (250, 250, 250)

        draw.rectangle([centro_x - 350, 0, centro_x + 350, 180], fill=bg_color_web)
        img_original.paste(logo_cabecera, (centro_x - (new_w_cab // 2), 30), logo_cabecera)

        if tipo_error == "no_mensajes":
            try:
                logo_triste = Image.open('/content/gatuflix_logo_triste.png').convert("RGBA")
                target_h_triste = 400
                new_w_triste = int(target_h_triste * (logo_triste.width / logo_triste.height))
                logo_triste = logo_triste.resize((new_w_triste, target_h_triste), Image.Resampling.LANCZOS)
                draw.rectangle([50, 300, ancho_total - 50, alto_total - 50], fill=bg_color_web)
                img_original.paste(logo_triste, (centro_x - (new_w_triste // 2), 350), logo_triste)
            except: pass

        ruta_editada = ruta_original.replace(".png", "_branded.png")
        img_original.save(ruta_editada)
        return ruta_editada
    except: return ruta_original

# --- FUNCIONES SELENIUM ---
def click_js(driver, elemento):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", elemento)
    except:
        elemento.click()

def verificar_cancelacion(chat_id, driver):
    if chat_id in estado_tareas and estado_tareas[chat_id] == False:
        try: driver.quit()
        except: pass
        return True
    return False

def tomar_foto_segura(driver, nombre_archivo, tipo_error="generico"):
    ruta = f"/content/{nombre_archivo}"
    try:
        _ = driver.current_url
        driver.save_screenshot(ruta)
        return editar_captura_con_gatuflix(ruta, tipo_error)
    except: return None

# --- LÓGICA DE EXTRACCIÓN ---
def obtener_codigo_nube(email_user, chat_id, status_callback=None):
    print(f"--- Procesando: {email_user} ---")
    if status_callback: status_callback("🚀 <b>Iniciando...</b>")

    # CONFIGURACIÓN CHROME PARA RAILWAY (Headless)
    options = webdriver.ChromeOptions()
    # En Railway, Chrome se instala en la ruta estándar. No necesitamos forzar binary_location
    # a menos que falle. Lo dejamos comentado, si Railway falla, lo activamos.
    options.binary_location = "/usr/bin/google-chrome" 
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)

    codigo_retorno = "No encontrado"
    ruta_foto = None
    tipo_resultado = "normal"

    try:
        if verificar_cancelacion(chat_id, driver): return "CANCELADO", None, "cancel"

        driver.get("https://bumbleegad.com/")
        if status_callback: status_callback("🔑 <b>Ingresando datos...</b>")

        input_email = wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
        input_email.clear()
        input_email.send_keys(email_user)

        btn_verify = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Verify')]")))
        click_js(driver, btn_verify)

        if status_callback: status_callback("📩 <b>Leyendo mensajes...</b>")

        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Ver')]")))
        except:
            ruta_foto = tomar_foto_segura(driver, 'error_no_mensajes.png', tipo_error="no_mensajes")
            driver.quit()
            return "No hay mensajes para mostrar.", ruta_foto, "error"

        time.sleep(2)
        botones_ver = driver.find_elements(By.XPATH, "//button[contains(text(), 'Ver')]")
        if botones_ver:
            click_js(driver, botones_ver[-1])
        else:
            driver.quit()
            return "Error: No hay mensajes.", None, "error"

        time.sleep(3)
        if verificar_cancelacion(chat_id, driver): return "CANCELADO", None, "cancel"

        accion_detectada = None
        boton_encontrado = None

        def buscar(contexto):
            try: return contexto.find_element(By.XPATH, "//*[contains(text(), 'Obtener')]"), "obtener"
            except: pass
            try: return contexto.find_element(By.XPATH, "//*[contains(text(), 'envié yo')]"), "si_envie"
            except: pass
            try: return contexto.find_element(By.XPATH, "//*[contains(text(), 'envie yo')]"), "si_envie"
            except: pass
            try: return contexto.find_element(By.XPATH, "//*[contains(text(), 'la envi')]"), "si_envie"
            except: pass
            return None, None

        boton_encontrado, accion_detectada = buscar(driver)

        if not boton_encontrado:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for frame in iframes:
                try:
                    driver.switch_to.frame(frame)
                    boton_encontrado, accion_detectada = buscar(driver)
                    if boton_encontrado:
                        click_js(driver, boton_encontrado)
                        driver.switch_to.default_content()
                        break
                    driver.switch_to.default_content()
                except: driver.switch_to.default_content()
        else:
            click_js(driver, boton_encontrado)

        if not accion_detectada:
            ruta_foto = tomar_foto_segura(driver, 'error_boton.png', tipo_error="generico")
            driver.quit()
            return "Error: No encontré botón de acción.", ruta_foto, "error"

        if accion_detectada == "obtener":
            if len(driver.window_handles) > 1: driver.switch_to.window(driver.window_handles[-1])
            time.sleep(5)
            cuerpo = driver.find_element(By.TAG_NAME, "body").text
            candidatos = re.findall(r'\b\d{4}\b', cuerpo)
            for num in candidatos:
                if not (num.startswith("202") and (num == "2024" or num == "2025")):
                    codigo_retorno = num
            if codigo_retorno == "No encontrado" and candidatos: codigo_retorno = candidatos[0]
            tipo_resultado = "codigo"
            ruta_foto = tomar_foto_segura(driver, 'exito_codigo.png', tipo_error="generico")

        elif accion_detectada == "si_envie":
            if status_callback: status_callback("🛡️ <b>Confirmando...</b>")
            if len(driver.window_handles) > 1: driver.switch_to.window(driver.window_handles[-1])
            time.sleep(3)
            try:
                btn_confirmar = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Confirmar actuali')]")))
                click_js(driver, btn_confirmar)
                time.sleep(3)
                codigo_retorno = "Listo, Dispositivo Verificado ✅"
                tipo_resultado = "mensaje"
            except:
                try:
                    btn_confirmar = driver.find_element(By.XPATH, "//*[contains(text(), 'Actualizar')]")
                    click_js(driver, btn_confirmar)
                    time.sleep(3)
                    codigo_retorno = "Listo, Dispositivo Verificado ✅"
                    tipo_resultado = "mensaje"
                except:
                    ruta_foto = tomar_foto_segura(driver, 'error_confirmar.png', tipo_error="generico")
                    driver.quit()
                    return "Error: No pude confirmar la actualización.", ruta_foto, "error"

            ruta_foto = tomar_foto_segura(driver, 'evidencia_final.png', tipo_error="generico")

    except Exception as e:
        ruta_foto = tomar_foto_segura(driver, 'error_crash.png', tipo_error="generico")
        codigo_retorno = f"Error técnico: {str(e)[:50]}"
        tipo_resultado = "error"

    finally:
        try: driver.quit()
        except: pass
        return codigo_retorno, ruta_foto, tipo_resultado

# --- TECLADOS TELEGRAM ---
def teclado_soporte_humano():
    markup = InlineKeyboardMarkup()
    url = f"https://wa.me/{NUMERO_SOPORTE}?text={urllib.parse.quote('Hola soporte. Fallo 3 veces. Adjunto captura:')}"
    markup.add(InlineKeyboardButton("📞 WhatsApp", url=url))
    markup.add(InlineKeyboardButton("Cancelar", callback_data="cancelar_limpio"))
    return markup
def teclado_cancelar():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⛔ Cancelar", callback_data="cancelar"))
    return markup
def teclado_reintentar(email):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 Reintentar", callback_data=f"retry|{email}"))
    return markup
def teclado_exito(codigo):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📋 Copiar Código", callback_data=f"copiar|{codigo}"))
    return markup
def teclado_tutorial_1():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Listo, seguir ➡", callback_data="tutorial_paso_2"))
    return markup
def teclado_tutorial_2():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Listo, seguir ➡", callback_data="tutorial_fin"))
    return markup

# --- MOTOR PRINCIPAL ---
def iniciar_proceso(message, email):
    chat_id = message.chat.id
    registrar_usuario(chat_id)

    if MODO_MANTENIMIENTO and not es_admin(chat_id):
        bot.send_message(chat_id, "🛠️ <b>Mantenimiento</b>", parse_mode="HTML"); return

    estado_tareas[chat_id] = True
    permitido, _ = verificar_limite(chat_id)
    if not permitido: bot.send_message(chat_id, "🚫 <b>Límite alcanzado</b>", parse_mode="HTML"); return

    esta_ocupado = candado_bot.locked()
    if esta_ocupado:
        cola_global.append({'chat_id': chat_id, 'msg_id': None, 'email': email})
        pos = len(cola_global)
        msg_espera = bot.send_message(chat_id, f"⏳ <b>En Fila (#{pos})</b>", parse_mode="HTML", reply_markup=teclado_cancelar())
        cola_global[-1]['msg_id'] = msg_espera.message_id
    else:
        info = "(Admin)" if es_admin(chat_id) else ""
        msg_espera = bot.send_message(chat_id, f"🔎 Buscando:\n<code>{email}</code> {info}", parse_mode="HTML", reply_markup=teclado_cancelar())

    with candado_bot:
        def actualizar_estado(texto_nuevo):
            try: bot.edit_message_text(f"{texto_nuevo}\n<code>{email}</code>", chat_id, msg_espera.message_id, parse_mode="HTML", reply_markup=teclado_cancelar())
            except: pass

        if esta_ocupado:
             cola_global[:] = [u for u in cola_global if u['chat_id'] != chat_id]
             actualizar_mensajes_cola()
             try: msg_espera = bot.send_message(chat_id, f"🚀 <b>¡Tu turno!</b>\n<code>{email}</code>", parse_mode="HTML", reply_markup=teclado_cancelar())
             except: pass

        texto, foto, tipo = obtener_codigo_nube(email, chat_id, status_callback=actualizar_estado)

    if chat_id in [u['chat_id'] for u in cola_global]: remover_de_cola(chat_id)
    if texto == "CANCELADO": return

    es_fracaso = "Error" in texto or "No encontrado" in texto or "técnico" in texto or "No hay mensajes" in texto
    if es_fracaso:
        registrar_fallo_sistema()
        registrar_en_sheets(chat_id, email, "FALLO", texto)
        msg_amigable = traducir_error_amigable(texto)
        if foto and os.path.exists(foto):
            try:
                with open(foto, 'rb') as f:
                    cap = msg_amigable
                    if "No hay mensajes" in texto: cap = "😿 <b>No hay mensajes recientes.</b>"
                    try: bot.delete_message(chat_id, msg_espera.message_id)
                    except: pass
                    bot.send_photo(chat_id, f, caption=cap, reply_markup=teclado_reintentar(email), parse_mode="HTML")
            except: bot.send_message(chat_id, msg_amigable, reply_markup=teclado_reintentar(email))
        else: bot.send_message(chat_id, f"{msg_amigable}\n(Sin captura)", reply_markup=teclado_reintentar(email))
    else:
        registrar_en_sheets(chat_id, email, "EXITO", texto)
        incrementar_uso(chat_id)
        contadores_retry[chat_id] = 0
        if tipo == "codigo": guardar_historial(chat_id, email, texto)
        try: bot.delete_message(chat_id, msg_espera.message_id)
        except: pass

        if foto and os.path.exists(foto):
            try:
                with open(foto, 'rb') as f:
                    cap_exito = ""
                    mk = None
                    if tipo == "codigo":
                        cap_exito = f"✅ <b>CÓDIGO:</b> <code>{texto}</code>"
                        mk = teclado_exito(texto)
                    else: cap_exito = f"✅ <b>{texto}</b>"
                    bot.send_photo(chat_id, f, caption=cap_exito, parse_mode="HTML", reply_markup=mk)
            except:
                if tipo == "codigo": bot.send_message(chat_id, f"✅ <code>{texto}</code>", parse_mode="HTML", reply_markup=teclado_exito(texto))
                else: bot.send_message(chat_id, f"✅ <b>{texto}</b>", parse_mode="HTML")
        else:
            if tipo == "codigo": bot.send_message(chat_id, f"✅ <code>{texto}</code>", parse_mode="HTML", reply_markup=teclado_exito(texto))
            else: bot.send_message(chat_id, f"✅ <b>{texto}</b>", parse_mode="HTML")

# --- HANDLERS ---
@bot.message_handler(commands=['historial'])
def mostrar_historial(message):
    chat_id = message.chat.id
    if not es_autorizado(chat_id): return
    if chat_id not in historial_usuarios or not historial_usuarios[chat_id]: bot.reply_to(message, "📭 Vacío."); return
    txt = "📜 <b>Historial:</b>\n\n"
    for e in reversed(historial_usuarios[chat_id]): txt += f"📅 {e['fecha']}\n📧 {e['correo']}\n🔑 <code>{e['codigo']}</code>\n\n"
    bot.reply_to(message, txt, parse_mode="HTML")

@bot.message_handler(commands=['start', 'ayuda'])
def send_welcome(message):
    registrar_usuario(message.chat.id)
    if not es_autorizado(message.chat.id): denegar_acceso(message.chat.id); return
    bot.reply_to(message, "👋 <b>Bienvenido</b>\nUsa /codigo", parse_mode="HTML")

@bot.message_handler(commands=['codigo'])
def iniciar_tutorial(message):
    chat_id = message.chat.id
    registrar_usuario(chat_id)
    if not es_autorizado(chat_id): denegar_acceso(chat_id); return
    permitido, _ = verificar_limite(chat_id)
    if not permitido: bot.send_message(chat_id, "🚫 Límite alcanzado."); return
    contadores_retry[chat_id] = 0
    try:
        with open('/content/tutorial_paso_1.png', 'rb') as f:
            bot.send_photo(chat_id, f, caption="📺 <b>Paso 1:</b>\nSeleccione <b>'Estoy de viaje'</b>. Si no aparece, seleccione <b>'Actualizar Hogar'</b>.", parse_mode="HTML", reply_markup=teclado_tutorial_1())
    except: bot.send_message(chat_id, "📺 <b>Paso 1:</b>\nSeleccione <b>'Estoy de viaje'</b>. Si no aparece, seleccione <b>'Actualizar Hogar'</b>.", parse_mode="HTML", reply_markup=teclado_tutorial_1())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if not es_autorizado(chat_id): return

    if call.data == "tutorial_paso_2":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        try:
            with open('/content/tutorial_paso_2.png', 'rb') as f:
                bot.send_photo(chat_id, f, caption="📧 <b>Paso 2:</b>\nSeleccione <b>'Enviar email'</b>.", parse_mode="HTML", reply_markup=teclado_tutorial_2())
        except: bot.send_message(chat_id, "📧 <b>Paso 2:</b>\nSeleccione <b>'Enviar email'</b>.", reply_markup=teclado_tutorial_2())
    elif call.data == "tutorial_fin":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        msg = bot.send_message(chat_id, "📧 <b>Listo.</b>\n\nPega el mensaje de entrega o el correo aquí:", parse_mode="HTML")
        bot.register_next_step_handler(msg, recibir_correo_paso_2)

    elif call.data == "cancelar":
        estado_tareas[chat_id] = False
        remover_de_cola(chat_id)
        contadores_retry[chat_id] = 0
        bot.answer_callback_query(call.id, "Cancelando...")
        try: bot.edit_message_text("🛑 Cancelado.", chat_id, call.message.message_id)
        except: pass
    elif call.data == "cancelar_limpio":
        contadores_retry[chat_id] = 0
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass

    elif call.data.startswith("retry|"):
        email_a = call.data.split("|")[1]
        intentos = contadores_retry.get(chat_id, 0) + 1
        contadores_retry[chat_id] = intentos
        if intentos > 2:
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            bot.send_message(chat_id, "🚫 <b>Problema Persistente</b>\nContacta a soporte.", parse_mode="HTML", reply_markup=teclado_soporte_humano())
            notificar_admins(f"🚨 <b>SOPORTE</b>\nCliente: {chat_id}\nFallo: 3 intentos.")
            registrar_en_sheets(chat_id, email_a, "CRITICO", "3 Intentos")
        else:
            bot.answer_callback_query(call.id, f"Reintentando ({intentos}/2)...")
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            threading.Thread(target=iniciar_proceso, args=(call.message, email_a)).start()

    elif call.data.startswith("copiar|"):
        codigo = call.data.split("|")[1]
        bot.send_message(chat_id, f"<code>{codigo}</code>", parse_mode="HTML")
        bot.answer_callback_query(call.id, "¡Enviado!")

def recibir_correo_paso_2(message):
    texto = message.text
    if texto.startswith("/"): bot.reply_to(message, "❌ Cancelado."); return
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', texto)
    if not emails:
        msg = bot.reply_to(message, "⚠️ No encontré correo. Intenta de nuevo:")
        bot.register_next_step_handler(msg, recibir_correo_paso_2)
        return
    email_final = emails[0]
    if len(texto) > 50: bot.reply_to(message, f"✅ Detectado: <code>{email_final}</code>", parse_mode="HTML")
    threading.Thread(target=iniciar_proceso, args=(message, email_final)).start()

@bot.message_handler(func=lambda m: True)
def chatbot(m):
    if not es_autorizado(m.chat.id): return
    txt = m.text.lower()
    if any(x in txt for x in ["hola", "buen"]): bot.reply_to(m, "¡Hola! 👋 Escribe /codigo.")
    elif any(x in txt for x in ["gracias", "grax"]): bot.reply_to(m, "¡De nada! 😺")
    else: bot.reply_to(m, "🤔 No entendí. Usa /codigo.")

print("--- BOT DE GATUFLIX (RAILWAY READY) ---")
try: bot.infinity_polling(timeout=90, long_polling_timeout=5)
except KeyboardInterrupt: print("🛑 BOT DETENIDO.")
except Exception as e: print(f"⚠️ Error: {e}")
