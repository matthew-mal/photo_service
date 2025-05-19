from django.db import models


class Photo(models.Model):
    file_name = models.CharField(max_length=255)
    random_number = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} - {self.random_number}"