from django.shortcuts import render
from .forms import UploadFileForm
from .models import FileRecord

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            # Proses file zip atau tif di sini sesuai kebutuhan Anda
            file_instance.save()

            # Catat informasi tentang file yang diunggah dalam FileRecord
            file_record = FileRecord(
                dir=file_instance.file.path,
                basename=file_instance.file.name,
                refname="Refname",  # Sesuaikan ini dengan nama referensi yang sesuai
                ekstension=file_instance.file.name.split('.')[-1],
                filesize=file_instance.file.size,
                added_to_geoserver=False,  # Diatur ke True jika ingin ditambahkan ke GeoServer
                url_geoserver="",  # URL GeoServer jika ditambahkan di sini
            )
            file_record.save()

            return render(request, 'upload_success.html')
    
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

def home(request):
    return render(request, 'home.html')  # Ganti 'home.html' dengan template yang sesuai


def upload_success(request):
    return render(request, 'upload_success.html')