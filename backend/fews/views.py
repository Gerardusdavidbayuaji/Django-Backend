import os
import zipfile
import requests
from django.shortcuts import render, redirect
from .forms import UploadFileForm
from .models import FileRecord

UPLOAD_DIR = 'backend/fews/repository'
MAX_FILE_SIZE = 200 * 1024 * 1024  # Max upload size 200 MB

def extract_zip(zip_file, destination):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(destination)

def handle_zip_file(f, upload_dir):
    extract_dir = os.path.join(upload_dir, os.path.splitext(f.name)[0])
    os.makedirs(extract_dir, exist_ok=True)
    extract_zip(f, extract_dir)
    return extract_dir

def handle_tif_file(f, upload_dir):
    tif_file_path = os.path.join(upload_dir, f.name)
    if os.path.exists(tif_file_path):
        os.remove(tif_file_path)
    with open(tif_file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return tif_file_path

def save_file_record(file_path, file_name, ekstension):
    filesize = os.path.getsize(file_path)
    dir_name = os.path.dirname(file_path).replace('\\','/')
    print("Directory name:", dir_name)
    
    record = FileRecord(
        dir=dir_name,
        basename=file_name,
        refname=file_name,
        ekstension=ekstension,
        filesize=filesize,
        added_to_geoserver=False,
        url_geoserver=""
    )
    record.save()

def get_shapefile_paths(directory):
    shapefile_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.shp') or file.endswith('.tif'):
                file_path = os.path.join(root, file).replace('\\', '/')
                print("test path", file_path)
                shapefile_paths.append((file_path, file))
    return shapefile_paths

workspace = "gsdb_simadu"
geoserver_enpoint = "http://admin:geoserver@127.0.0.1:8080/geoserver"

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

def handle_uploaded_file(f):
    if f.size > MAX_FILE_SIZE:
        return False

    try:
        if f.name.endswith('.zip'):
            extracted_dir = handle_zip_file(f, UPLOAD_DIR)
            shapefile_paths = get_shapefile_paths(extracted_dir)

            for file_path, file_name in shapefile_paths:
                file_extension = os.path.splitext(file_name)[1]
                save_file_record(file_path, file_name, file_extension)
                if file_extension == '.shp' or file_extension == '.tif':
                    global data_path
                    global store
                    data_path = file_path
                    print("data path", data_path)
                    store = os.path.splitext(file_name)[0]  # Using the basename without extension
                    print("store", store)
                upload_to_geoserver(file_path, file_name, workspace, store, geoserver_enpoint)

            return True
    except Exception as e:
        print(f"Error handling file: {e}")
        return False

    return False

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            if handle_uploaded_file(uploaded_file):
                return redirect('upload_success')
            else:
                error_message = "Failed to handle the uploaded file."
                return render(request, 'upload.html', {'form': form, 'error_message': error_message})
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

def upload_success(request):
    return render(request, 'upload_success.html')

def home(request):
    return redirect('upload_file')
