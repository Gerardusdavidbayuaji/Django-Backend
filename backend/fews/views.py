import os
import zipfile
from django.shortcuts import render, redirect
from .forms import UploadFileForm

UPLOAD_DIR = 'backend/fews/repository'
MAX_FILE_SIZE = 200 * 1024 * 1024  # maksimal upload data ukuran 200 MB

def extract_zip(zip_file, destination):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(destination)

def handle_zip_file(f, upload_dir):
    extract_dir = os.path.join(upload_dir, os.path.splitext(f.name)[0])
    os.makedirs(extract_dir, exist_ok=True)
    extract_zip(f, extract_dir)
    return True

def handle_tif_file(f, upload_dir):
    tif_file_path = os.path.join(upload_dir, f.name)
    if os.path.exists(tif_file_path):
        os.remove(tif_file_path)
    with open(tif_file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return True

def handle_uploaded_file(f):
    if f.size > MAX_FILE_SIZE:
        return False
    
    try:
        if f.name.endswith('.zip'):
            return handle_zip_file(f, UPLOAD_DIR)
        elif f.name.endswith('.tif'):
            return handle_tif_file(f, UPLOAD_DIR)
    except Exception as e:
        print(f"Error handling file: {e}")
        return False

    return False  # tidak support type data

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
