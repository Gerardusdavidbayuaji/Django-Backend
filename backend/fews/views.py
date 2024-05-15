import zipfile
from django.shortcuts import render, redirect
from .forms import UploadFileForm
from .models import UploadedFile
from django.core.files.storage import FileSystemStorage
import os

def handle_uploaded_file(f):
    upload_dir = 'backend/fews/repository'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    with open(os.path.join(upload_dir, f.name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    # Extract the zip file
    with zipfile.ZipFile(os.path.join(upload_dir, f.name), 'r') as zip_ref:
        zip_ref.extractall(upload_dir)

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            form.save()
            return redirect('upload_success')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

def upload_success(request):
    return render(request, 'upload_success.html')

def home(request):
    return redirect('upload_file')
