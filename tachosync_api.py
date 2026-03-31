import http.client
import requests
import os

headers = { 'X-Api-Key': "rxTw4lbgDY+wrQEXHfJ8ABrjCKmzTv3L7J3jKC9bI0g=" }
download_path_vehicles = r"C:\Users\JRSS\Downloads\Tacho_Files\Tacho_Vehicles"
download_path_drivers = r"C:\Users\JRSS\Downloads\Tacho_Files\Tacho_Drivers"

get_vehicles_url = "https://api.tacho.teltonika.lt/v1/Vehicles"
get_drivers_url = "https://api.tacho.teltonika.lt/v1/Drivers"
get_vehicles_with_file_url = "https://api.tacho.teltonika.lt/v1/VehicleFiles/Filters"
get_drivers_with_file_url = "https://api.tacho.teltonika.lt/v1/DriverFiles/Filters"
get_vehicle_files_url = "https://api.tacho.teltonika.lt/v1/VehicleFiles"
get_driver_files_url = "https://api.tacho.teltonika.lt/v1/DriverFiles"
download_vehicle_files_url = "https://api.tacho.teltonika.lt/v1/VehicleFiles/Download"
download_driver_files_url = "https://api.tacho.teltonika.lt/v1/DriverFiles/Download"


def get_companies(headers):
    url = "https://api.tacho.teltonika.lt/v1/Companies"
    response = requests.get(url, headers=headers)
    response = response.json()
    childCompanies = response['childCompanies']
    '''for company in childCompanies:
        print(f"ID: {company['id']}, Name: {company['name']}")'''
    return childCompanies

def get_entries(headers, url, pagenumber, pagesize, companies):
    entries = {}
    for company in companies:
        querystring = {"PageNumber": pagenumber, "PageSize": pagesize, "CompanyId": company['id']}
        response = requests.get(url, headers=headers, params=querystring)
        response = response.json()
        entries_temp = response['items']
        for entry in entries_temp:
            # print(f"ID: {vehicle['id']}, Name: {vehicle['number']}")
            entries[entry['id']] = entry
    return entries

def get_drivers_ordered(headers, url, orderby, descending, pagenumber, pagesize, companies):
    entries = {}
    for company in companies:
        querystring = {"OrderBy": orderby, "Descending": descending, "PageNumber": pagenumber, "PageSize": pagesize, "CompanyId": company['id']}
        response = requests.get(url, headers=headers, params=querystring)
        response = response.json()
        entries_temp = response['items']
        for entry in entries_temp:
            print(f"updatedAt: {entry['updatedAt']}, company: {entry['company']['name']}, cardNumber: {entry['cardNumber']}, cardName: {entry['cardName']}")
            entries[entry['id']] = entry
    return entries


def get_entries_with_files(headers, url, companies):
    entries = []
    for company in companies:
        querystring = {"CompanyId": company['id']}
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            print(f"Error consultando companyId {company}: {response.status_code}")
            continue
        entries_temp = response.json()
        if not entries_temp:
            continue
        for item in entries_temp:
            entries.append({
                "entry_id": item['id'],
                "entry_name": item['name'],
                "company_id": company['id'],
                "company_name": company['name'],
            })
    return entries


def get_files(headers, url):
    querystring = {"AllCompanies": True, "PageNumber": 1, "PageSize": 100}
    response = requests.get(url, headers=headers, params=querystring)
    files = response.json()
    return files


def download_files(headers, files, url, download_path):
    # headers = {"X-Api-Key": "rxTw4lbgDY+wrQEXHfJ8ABrjCKmzTv3L7J3jKC9bI0g="}
    for item in files:
        ids = []
        ids.append(item['id'])
        querystring = {"Ids": ids}
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            # Crear ruta destino
            file_path = os.path.join(download_path, item['fileName'])
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Archivo descargado correctamente: {file_path}")
            '''with open(item['fileName'], "wb") as f:
                f.write(response.content)
            print(f"Archivo descargado correctamente: {item['fileName']}")'''
        else:
            print(f"Error al descargar: {response.status_code} - {response.text}")


if __name__ == "__main__":
    companies = get_companies(headers)
    # vehicles = get_entries(headers, get_vehicles_url, 1, 100, companies)
    # drivers = get_entries(headers, get_drivers_url, 1, 100, companies)
    drivers_orderedBy_UpdatedAt = get_drivers_ordered(headers, get_drivers_url, "UpdatedAt", "true", 1, 100, companies)
    # vehicles_with_files = get_entries_with_files(headers, get_vehicles_with_file_url, companies)
    # drivers_with_files = get_entries_with_files(headers, get_drivers_with_file_url, companies)
    # vehicle_files = get_files(headers, 1, 100, get_vehicle_files_url)
    # driver_files = get_files(headers, 1, 100, get_driver_files_url)
    # download_files(headers, vehicle_files, download_vehicle_files_url, download_path_vehicles)
    # download_files(headers, driver_files, download_driver_files_url, download_path_drivers)
