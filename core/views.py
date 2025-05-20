from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Photo
from .tasks import process_photo


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photos'] = Photo.objects.all().order_by('-uploaded_at')
        return context


class UploadPhotoView(APIView):
    def post(self, request):
        photo = request.FILES.get('photo')
        if not photo:
            return Response(
                {'error': 'Файл не предоставлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_name = photo.name
        photo_instance = Photo.objects.create(file_name=file_name, random_number=0)
        process_photo.delay(photo_instance.id, file_name)

        return Response(
            {'message': 'Файл принят, обработка начата'},
            status=status.HTTP_202_ACCEPTED
        )


class BulkUploadView(APIView):
    def post(self, request):
        photo = request.FILES.get('photo')
        if not photo:
            return Response(
                {'error': 'Файл не предоставлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_name = photo.name
        for i in range(100):
            photo_instance = Photo.objects.create(file_name=f"{file_name}_{i}")
            process_photo.delay(photo_instance.id, f"{file_name}_{i}")

        return Response(
            {'message': '100 задач на обработку запущено'},
            status=status.HTTP_202_ACCEPTED
        )