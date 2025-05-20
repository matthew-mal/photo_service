from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from .models import Photo
from .tasks import process_photo
import logging

logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["photos"] = Photo.objects.all().order_by("-uploaded_at")
        return context


class UploadPhotoView(APIView):
    def post(self, request):
        photo = request.FILES.get("photo")
        if not photo:
            logger.error("No photo provided in request")
            return Response(
                {"error": "Пожалуйста, выберите файл для загрузки"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_name = photo.name
        logger.info(f"Processing file: {file_name}")
        photo_instance = Photo.objects.create(file_name=file_name, random_number=0)
        process_photo.delay(photo_instance.id, file_name)
        logger.info(f"Task queued for photo_id: {photo_instance.id}")
        if request.htmx:
            return render(
                request,
                "table.html",
                {
                    "photos": Photo.objects.all().order_by("-uploaded_at"),
                    "message": "Файл в обработке",
                },
            )
        return Response(
            {"message": "Файл в обработке"}, status=status.HTTP_202_ACCEPTED
        )


class BulkUploadView(APIView):
    def post(self, request):
        photo = request.FILES.get("photo")
        if not photo:
            logger.error("No photo provided in request for bulk upload")
            return Response(
                {"error": "Пожалуйста, выберите файл для загрузки"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_file_name = photo.name
        logger.info(f"Starting bulk upload with base file: {base_file_name}")
        for i in range(100):
            file_name = f"{base_file_name.rsplit('.', 1)[0]}_{i}.{base_file_name.rsplit('.', 1)[1]}"
            photo_instance = Photo.objects.create(file_name=file_name, random_number=0)
            process_photo.delay(photo_instance.id, file_name)
        if request.htmx:
            return render(
                request,
                "table.html",
                {
                    "photos": Photo.objects.all().order_by("-uploaded_at"),
                    "message": "Файл в обработке",
                },
            )
        return Response(
            {"message": "Файл в обработке"}, status=status.HTTP_202_ACCEPTED
        )


class StatusView(APIView):
    def get(self, request):
        total = Photo.objects.count()
        processed = Photo.objects.filter(random_number__gt=0).count()
        return Response({"processed": processed, "total": total})


class ListPhotosView(APIView):
    def get(self, request):
        photos = Photo.objects.all().order_by("-uploaded_at")
        paginator = Paginator(photos, 50)
        page = request.GET.get("page", 1)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return render(request, "table.html", {
            "photos": page_obj,
            "page_obj": page_obj,
        })
