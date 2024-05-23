import os
import requests
from django.shortcuts import render
from .forms import UploadFileForm
from .models import FileRecord
import zipfile

def extract_zip(file_path, extract_path):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

def process_zip_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.zip'):
            file_path = os.path.join(directory, filename)
            print('file path', file_path)
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
                        print("Path file SHP:", shp_path)
                        # Do something with SHP file here
                        upload_to_geoserver(shp_path, "shp")
                    elif file.endswith('.tif'):
                        tif_path = file_path.replace('\\', '/')
                        print("Path file TIF:", tif_path)
                        # Do something with TIF file here
                        upload_to_geoserver(tif_path, "geotiff")

    # After handling all files, retrieve TIF files from the repository folder
    repository_path = 'C:\\GD\\1_Testing\\upload_fews\\backend\\fews\\repository'
    for filename in os.listdir(repository_path):
        if filename.endswith('.tif'):
            tif_path = os.path.join(repository_path, filename)
            tif_path = tif_path.replace('\\','/')
            print("Path file TIF from repository:", tif_path)
            # Do something with TIF file from repository here
            upload_to_geoserver(tif_path, "geotiff")

def upload_to_geoserver(file_path, file_type):
    geoserver_endpoint = "http://admin:geoserver@127.0.0.1:8080/geoserver"
    workspace = "gsdb_simadu"

    # Extract basename from file_path
    basename = os.path.basename(file_path)
    store = os.path.splitext(basename)[0]  # Use basename as store name
    store_type = "datastores" if file_type == 'shp' else "coveragestores"

    # URL of the file to be accessed by GeoServer
    file_url = f"file://{file_path.replace(os.sep, '/')}"
    
    # Construct URL for GeoServer REST API
    url = f"{geoserver_endpoint}/rest/workspaces/{workspace}/{store_type}/{store}/external.{file_type}"

    # Construct data payload for the PUT request
    data = file_url
    print("data to geoserver", data)

    # Make PUT request to GeoServer
    headers = {"Content-type": "text/plain"}
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()  # Will raise an HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
        return False

    # Check if upload was successful
    if response.status_code in (201, 202):
        print(f"Successful upload to GeoServer: {file_path}")
        return True
    else:
        print(f"Failed upload to GeoServer: {file_path}, Status Code: {response.status_code}, Response: {response.text}")
        return False

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

            process_zip_files('C:\\GD\\1_Testing\\upload_fews\\backend\\fews\\repository')

            return render(request, 'upload_success.html')
    
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

def home(request):
    return render(request, 'home.html')

def upload_success(request):
    return render(request, 'upload_success.html')
