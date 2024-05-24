import json
import os
import requests
from django.http import JsonResponse
from django.shortcuts import render
from .forms import UploadFileForm
from .models import FileRecord
import zipfile
from owslib.wms import WebMapService

def extract_zip(file_path, extract_path):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

def process_zip_files(directory):
    uploaded_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.zip'):
            file_path = os.path.join(directory, filename)
            folder_name = os.path.splitext(filename)[0]
            extract_path = os.path.join(directory, folder_name)
            os.makedirs(extract_path, exist_ok=True)
            extract_zip(file_path, extract_path)
            os.remove(file_path)

            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file.endswith('.shp'):
                        shp_path = file_path.replace('\\', '/')
                        if upload_to_geoserver(shp_path, "shp"):
                            uploaded_files.append(shp_path)
                    elif file.endswith('.tif'):
                        tif_path = file_path.replace('\\', '/')
                        if upload_to_geoserver(tif_path, "geotiff"):
                            uploaded_files.append(tif_path)

    repository_path = 'C:\\GD\\1_Testing\\upload_fews\\backend\\fews\\repository'
    for filename in os.listdir(repository_path):
        if filename.endswith('.tif'):
            tif_path = os.path.join(repository_path, filename)
            tif_path = tif_path.replace('\\', '/')
            if upload_to_geoserver(tif_path, "geotiff"):
                uploaded_files.append(tif_path)
                
    return uploaded_files

def upload_to_geoserver(file_path, file_type):
    geoserver_endpoint = "http://admin:geoserver@127.0.0.1:8080/geoserver"
    workspace = "gsdb_simadu"

    basename = os.path.basename(file_path)
    store = os.path.splitext(basename)[0]
    store_type = "datastores" if file_type == 'shp' else "coveragestores"

    file_url = f"file://{file_path.replace(os.sep, '/')}"
    url = f"{geoserver_endpoint}/rest/workspaces/{workspace}/{store_type}/{store}/external.{file_type}"

    data = file_url
    headers = {"Content-type": "text/plain"}
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return False

    if response.status_code in (201, 202):
        return True
    else:
        return False

def get_bounding_box(url, layer_name):
    params = {}
    wms = WebMapService(url, version='1.1.1')
    bounds = wms[layer_name].boundingBox
    if bounds is None:
        bounds = wms[layer_name].boundingBoxWGS84
        crs = 'EPSG:4326'
    else:
        crs = bounds[4]
    bbox = ",".join([str(b) for b in bounds[:4]])
    params['bbox'] = bbox
    params['srs'] = crs
    params['transparent'] = 'true'
    params['width'] = '768'
    params['height'] = '330'
    return "&".join([f"{k}={v}" for k, v in params.items()])

def get_url_geoserver(geoserver_endpoint, workspace, store):
    layer_name = f"{workspace}:{store}"
    params = get_bounding_box(geoserver_endpoint + '/wms', layer_name)

    url_geoserver = {
        "wms": f"{geoserver_endpoint}/{workspace}/wms?service=WMS&version=1.1.0&request=GetMap&layers={workspace}:{store}&{params}&format=image/png",  
        "wfs": f"{geoserver_endpoint}/{workspace}/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={workspace}:{store}&outputFormat=application/json",
        "data_vektor": f"{geoserver_endpoint}/{workspace}/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={workspace}:{store}&outputFormat=shape-zip",
        "data_raster": f"{geoserver_endpoint}/{workspace}/wms?service=WMS&version=1.1.0&request=GetMap&layers={workspace}:{store}&{params}&format=image/geotiff", 
        "wms_style": f"{geoserver_endpoint}/{workspace}/wms?service=WMS&version=1.1.0&request=GetMap&layers={workspace}:{store}&styles=gsdb_simadu:curah_hujan_jawa&{params}&format=image/png",  
    }
    return url_geoserver

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.save()

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

            uploaded_files = process_zip_files('C:\\GD\\1_Testing\\upload_fews\\backend\\fews\\repository')

            geoserver_urls = []
            for file in uploaded_files:
                basename = os.path.basename(file)
                store = os.path.splitext(basename)[0]
                url_geoserver = get_url_geoserver("http://127.0.0.1:8080/geoserver", "gsdb_simadu", store)
                # Pass layer name to the response
                geoserver_urls.append({
                    "file": file,
                    "layerName": store,  # Include the layer name in the response
                    "urls": url_geoserver
                })

            return JsonResponse({"status": "success", "geoserver_urls": geoserver_urls})

    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


def home(request):
    return render(request, 'home.html')

def upload_success(request):
    return render(request, 'upload_success.html')
