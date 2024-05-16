import os
import zipfile
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

def handle_uploaded_file(f):
    if f.size > MAX_FILE_SIZE:
        return False

    try:
        if f.name.endswith('.zip'):
            extracted_dir = handle_zip_file(f, UPLOAD_DIR)
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    if file.endswith('.shp'):
                        file_path = os.path.join(root, file)
                        save_file_record(file_path, file, os.path.splitext(file)[1])
            return True
        elif f.name.endswith('.tif'):
            file_path = handle_tif_file(f, UPLOAD_DIR)
            save_file_record(file_path, f.name, '.tif')
            return True
    except Exception as e:
        print(f"Error handling file: {e}")
        return False

    return False  # unsupported file type

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
