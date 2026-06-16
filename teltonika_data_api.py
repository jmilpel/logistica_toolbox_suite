import requests
import pandas as pd
import os

API_URL = "https://api.teltonika.lt/devices/"


def load_imeis(file_path):
    """Carga los IMEIs desde TXT, CSV o Excel devolviendo una lista limpia."""
    imeis = []
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    try:
        if ext == '.xlsx':
            df = pd.read_excel(file_path, header=None)
            imeis = df.iloc[:, 0].astype(str).tolist()
        elif ext == '.csv':
            df = pd.read_csv(file_path, header=None)
            imeis = df.iloc[:, 0].astype(str).tolist()
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                imeis = [line.strip() for line in f if line.strip()]

        # Limpieza básica: quitar espacios y verificar que sean solo dígitos
        imeis = [imei.strip() for imei in imeis if imei.strip().isdigit()]
        return imeis
    except Exception as e:
        print(f"Error cargando IMEIs: {e}")
        return None


def query_api(imei, token):
    """Consulta la API de Teltonika para un IMEI concreto."""
    url = f"{API_URL}{imei}"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Código {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def extract_field_data(response_data, field):
    """Extrae de forma segura el campo solicitado del JSON de respuesta."""
    if "error" in response_data:
        return ""

    try:
        if field == "vin" and "obd" in response_data:
            return response_data["obd"].get("vin", "")
        elif field == "iccid":
            iccid = response_data.get("iccid", "")
            if iccid and len(iccid) >= 19:
                return iccid[:19]
            return iccid
        elif field == "group" and "group" in response_data:
            group = response_data.get("group", {})
            return group.get('name', "")
        else:
            return str(response_data.get(field, ""))
    except Exception as e:
        return ""
