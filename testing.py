# from django.test import TestCase

# # Create your tests here.

import os
from urllib import response
import requests

workspace = "gsdb_simadu"
geoserver_enpoint = "http://admin:geoserver@127.0.0.1:8080/geoserver"
file_type = 'C:/GD/1_Testing/upload_fews/backend/fews/repository/batas_provinsi/batas_provinsi.shp'

def upload_to_geoserver(data_path, file_name, workspace, store, geoserver_endpoint):
    file_type = os.path.splitext(file_name)[1][1:]
    print('test', file_type)
    store_type = "datastores" if file_type == 'shp' else "coveragestores"
    url = f"{geoserver_endpoint}/rest/workspaces/{workspace}/{store_type}/{store}/external.{file_type}"

    with open(data_path, 'rb') as data:
        headers = {"Content-type": "text/plain" if file_type == 'shp' else "image/tiff"}
        response = requests.put(url, data=data, headers=headers)

    if response.status_code == 201:
        print(f"Successfully uploaded {file_name} to GeoServer.")
    else:
        print(f"Failed to upload {file_name} to GeoServer. Status code: {response.status_code}")
        print(response.text)

import requests

geoserver_enpoint = "http://admin:geoserver@127.0.0.1:8080/geoserver"
workspace = "gsdb_simadu"

store = "test-store1"
data = f"C:/GD/1_Testing/upload_fews/backend/fews/repository/provinsi_jateng/provinsi_jateng.shp"
file_type = "shp"
store_type = "datastores" if file_type == 'shp' else "coveragestores"

url = f"{geoserver_enpoint}/rest/workspaces/{workspace}/{store_type}/{store}/external.{file_type}"

headers = {"Content-type": "text/plain"}
requests.put(url, data=data, headers=headers)


print(f"Request URL: {url}")
print(f"Headers: {headers}")