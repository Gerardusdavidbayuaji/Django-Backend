import os
import requests
import zipfile
from owslib.wms import WebMapService
from django.http import JsonResponse
from django.shortcuts import render
from .forms import UploadFileForm
from .models import FileRecord

GEOSERVER_ENDPOINT = "http://admin:geoserver@127.0.0.1:8080/geoserver"
WORKSPACE = "gsdb_simadu"
REPOSITORY_PATH = 'C:\\GD\\1_Testing\\upload_fews\\backend\\fews\\repository'

def extract_zip(file_path, extract_path):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

def process_zip_files(directory):
    uploaded_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.zip'):
            extract_path = extract_zip_file(directory, filename)
            remove_file(directory, filename)
            uploaded_files.extend(process_extracted_files(extract_path))
    uploaded_files.extend(process_repository_files())
    return uploaded_files

def extract_zip_file(directory, filename):
    file_path = os.path.join(directory, filename)
    folder_name = os.path.splitext(filename)[0]
    extract_path = os.path.join(directory, folder_name)
    os.makedirs(extract_path, exist_ok=True)
    extract_zip(file_path, extract_path)
    return extract_path

def remove_file(directory, filename):
    file_path = os.path.join(directory, filename)
    os.remove(file_path)

def process_extracted_files(extract_path):
    uploaded_files = []
    for root, _, files in os.walk(extract_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.shp'):
                if upload_to_geoserver(file_path, "shp"):
                    uploaded_files.append((file_path, "shp"))
            elif file.endswith('.tif'):
                if upload_to_geoserver(file_path, "geotiff"):
                    uploaded_files.append((file_path, "geotiff"))
    return uploaded_files

def process_repository_files():
    uploaded_files = []
    for filename in os.listdir(REPOSITORY_PATH):
        if filename.endswith('.tif'):
            file_path = os.path.join(REPOSITORY_PATH, filename)
            if upload_to_geoserver(file_path, "geotiff"):
                uploaded_files.append((file_path, "geotiff"))
    return uploaded_files

def upload_to_geoserver(file_path, file_type):
    store_type = "datastores" if file_type == 'shp' else "coveragestores"
    store = os.path.splitext(os.path.basename(file_path))[0]
    file_url = f"file://{file_path.replace(os.sep, '/')}"
    url = f"{GEOSERVER_ENDPOINT}/rest/workspaces/{WORKSPACE}/{store_type}/{store}/external.{file_type}"

    headers = {"Content-type": "text/plain"}
    try:
        response = requests.put(url, data=file_url, headers=headers)
        response.raise_for_status()
        return response.status_code in (201, 202)
    except requests.exceptions.RequestException:
        return False

def get_bounding_box(url, layer_name):
    wms = WebMapService(url, version='1.1.1')
    bounds = wms[layer_name].boundingBox or wms[layer_name].boundingBoxWGS84
    crs = bounds[4] if bounds else 'EPSG:4326'
    bbox = ",".join(map(str, bounds[:4]))
    return f"bbox={bbox}&srs={crs}&transparent=true&width=768&height=330"

def get_url_geoserver(store):
    layer_name = f"{WORKSPACE}:{store}"
    params = get_bounding_box(f"{GEOSERVER_ENDPOINT}/wms", layer_name)
    return {
        "wms": f"{GEOSERVER_ENDPOINT}/{WORKSPACE}/wms?service=WMS&version=1.1.0&request=GetMap&layers={layer_name}&{params}&format=image/png",  
        "wfs": f"{GEOSERVER_ENDPOINT}/{WORKSPACE}/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={layer_name}&outputFormat=application/json",
        "data_vektor": f"{GEOSERVER_ENDPOINT}/{WORKSPACE}/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={layer_name}&outputFormat=shape-zip",
        "data_raster": f"{GEOSERVER_ENDPOINT}/{WORKSPACE}/wms?service=WMS&version=1.1.0&request=GetMap&layers={layer_name}&{params}&format=image/geotiff", 
        "wms_style": f"{GEOSERVER_ENDPOINT}/{WORKSPACE}/wms?service=WMS&version=1.1.0&request=GetMap&layers={layer_name}&styles=gsdb_simadu:curah_hujan_id&{params}&format=image/png",  
    }

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = save_file_instance(form)
            save_file_record(file_instance)
            uploaded_files = process_zip_files(REPOSITORY_PATH)
            geoserver_urls = get_geoserver_urls(uploaded_files)
            return JsonResponse({"status": "success", "geoserver_urls": geoserver_urls})
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

def save_file_instance(form):
    file_instance = form.save(commit=False)
    file_instance.save()
    return file_instance

def save_file_record(file_instance):
    file_path = file_instance.file.path
    file_name = os.path.basename(file_instance.file.name)
    file_record = FileRecord(
        dir=file_path,
        basename=file_name,
        refname="Refname",
        ekstension=file_name.split('.')[-1],
        filesize=file_instance.file.size,
        added_to_geoserver=False,
        url_geoserver="",
    )
    file_record.save()

def get_geoserver_urls(uploaded_files):
    geoserver_urls = []
    for file, file_type in uploaded_files:
        store = os.path.splitext(os.path.basename(file))[0]
        url_geoserver = get_url_geoserver(store)
        geoserver_urls.append({
            "file": file,
            "file_type": file_type,
            "layerName": store,
            "urls": url_geoserver
        })
    return geoserver_urls

def home(request):
    return render(request, 'home.html')
