from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to='backend/fews/repository')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class FileRecord(models.Model):
    dir = models.CharField(max_length=255)
    basename = models.CharField(max_length=255)
    refname = models.CharField(max_length=255)
    ekstension = models.CharField(max_length=10)
    filesize = models.BigIntegerField()
    added_to_geoserver = models.BooleanField(default=False)
    url_geoserver = models.URLField()  

    def __str__(self):
        return self.basename