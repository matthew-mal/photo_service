import pytest
import logging
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from rest_framework.test import APIClient
from unittest.mock import patch
from core.models import Photo
from core.tasks import process_photo
from core.telegram import send_telegram_notification

# Setup logging for tests
logger = logging.getLogger(__name__)


# Fixture for APIClient
@pytest.fixture
def api_client():
    return APIClient()


# Fixture for Django test Client (for template and context checks)
@pytest.fixture
def client():
    return Client()


# Fixture for creating a Photo instance
@pytest.fixture
def photo():
    return Photo.objects.create(file_name="test.jpg", random_number=0)


# Fixture for mocking Celery task
@pytest.fixture
def mock_celery_task():
    with patch("core.views.process_photo") as mock_task:
        yield mock_task


# Fixture for mocking Telegram notification
@pytest.fixture
def mock_telegram_notification():
    with patch("core.tasks.send_telegram_notification") as mock_notification:
        yield mock_notification


# Tests for IndexView
@pytest.mark.django_db
class TestIndexView:
    def test_index_view_renders_template(self, client):
        response = client.get(reverse("index"))
        assert response.status_code == 200
        assert "index.html" in [t.name for t in response.templates]

    def test_index_view_context_contains_photos(self, client, photo):
        response = client.get(reverse("index"))
        assert response.status_code == 200
        assert "photos" in response.context
        assert response.context["photos"].count() == 1
        assert response.context["photos"][0].file_name == "test.jpg"


# Tests for UploadPhotoView
@pytest.mark.django_db
class TestUploadPhotoView:
    def test_upload_photo_success(self, api_client, mock_celery_task):
        photo = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        response = api_client.post(
            reverse("upload"), {"photo": photo}, format="multipart"
        )
        assert response.status_code == 202
        assert response.data == {"message": "Файл в обработке"}
        assert Photo.objects.count() == 1
        assert Photo.objects.first().file_name == "test.jpg"
        mock_celery_task.delay.assert_called_once()

    def test_upload_photo_no_file(self, api_client):
        response = api_client.post(reverse("upload"), {}, format="multipart")
        assert response.status_code == 400
        assert response.data == {"error": "Пожалуйста, выберите файл для загрузки"}
        assert Photo.objects.count() == 0

    def test_upload_photo_htmx(self, client, mock_celery_task):
        photo = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        response = client.post(
            reverse("upload"), {"photo": photo}, HTTP_HX_REQUEST="true"
        )
        assert response.status_code == 200
        assert "table.html" in [t.name for t in response.templates]
        assert "photos" in response.context
        assert response.context["message"] == "Файл в обработке"
        assert Photo.objects.count() == 1
        mock_celery_task.delay.assert_called_once()


# Tests for BulkUploadView
@pytest.mark.django_db
class TestBulkUploadView:
    def test_bulk_upload_success(self, api_client, mock_celery_task):
        photo = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        response = api_client.post(
            reverse("bulk-upload"), {"photo": photo}, format="multipart"
        )
        assert response.status_code == 202
        assert response.data == {"message": "Файл в обработке"}
        assert Photo.objects.count() == 100
        assert Photo.objects.first().file_name == "test_0.jpg"
        assert mock_celery_task.delay.call_count == 100

    def test_bulk_upload_no_file(self, api_client):
        response = api_client.post(reverse("bulk-upload"), {}, format="multipart")
        assert response.status_code == 400
        assert response.data == {"error": "Пожалуйста, выберите файл для загрузки"}
        assert Photo.objects.count() == 0

    def test_bulk_upload_htmx(self, client, mock_celery_task):
        photo = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        response = client.post(
            reverse("bulk-upload"), {"photo": photo}, HTTP_HX_REQUEST="true"
        )
        assert response.status_code == 200
        assert "table.html" in [t.name for t in response.templates]
        assert "photos" in response.context
        assert response.context["message"] == "Файл в обработке"
        assert Photo.objects.count() == 100
        assert mock_celery_task.delay.call_count == 100


# Tests for StatusView
@pytest.mark.django_db
class TestStatusView:
    def test_status_view(self, api_client, photo):
        Photo.objects.create(file_name="test2.jpg", random_number=100)
        response = api_client.get(reverse("status"))
        assert response.status_code == 200
        assert response.data == {"processed": 1, "total": 2}


# Tests for ListPhotosView
@pytest.mark.django_db
class TestListPhotosView:
    def test_list_photos_view(self, client, photo):
        response = client.get(reverse("list_photos"))
        assert response.status_code == 200
        assert "table.html" in [t.name for t in response.templates]
        assert "photos" in response.context
        assert response.context["photos"].count() == 1
        assert response.context["photos"][0].file_name == "test.jpg"


# Tests for process_photo task
@pytest.mark.django_db
class TestProcessPhotoTask:
    @patch("core.tasks.time.sleep")
    @patch("core.tasks.random.randint", return_value=42)
    def test_process_photo_success(
        self, mock_randint, mock_sleep, photo, mock_telegram_notification
    ):
        for i in range(19):
            Photo.objects.create(file_name=f"test{i}.jpg", random_number=0)
        process_photo(photo.id, "test.jpg")
        photo.refresh_from_db()
        assert photo.random_number == 42
        mock_sleep.assert_called_once_with(20)
        mock_randint.assert_called_once_with(1, 2000)
        mock_telegram_notification.assert_called_once_with(
            "Обработано 20 файлов! Последний: test.jpg, число: 42"
        )

    def test_process_photo_not_found(self, caplog):
        caplog.set_level(logging.ERROR, logger="core.tasks")
        process_photo(999, "test.jpg")
        assert "Photo 999 not found" in caplog.text

    def test_photo_str(self, photo):
        assert str(photo) == "test.jpg - 0"

    @patch("core.tasks.Photo.save", side_effect=Exception("Test error"))
    def test_process_photo_generic_exception(self, mock_save, photo, caplog):
        caplog.set_level(logging.ERROR, logger="core.tasks")
        process_photo(photo.id, photo.file_name)
        assert "Test error" in caplog.text


# Tests for send_telegram_notification
@pytest.mark.asyncio
async def test_send_telegram_notification_success():
    with patch("core.telegram.telegram.Bot.send_message") as mock_send:
        await send_telegram_notification("Test message")
        mock_send.assert_called_once_with(chat_id="CHAT_ID", text="Test message")


@pytest.mark.asyncio
async def test_send_telegram_notification_failure(caplog):
    caplog.set_level(logging.ERROR, logger="core.telegram")
    with patch(
        "core.telegram.telegram.Bot.send_message",
        side_effect=Exception("Telegram error"),
    ):
        await send_telegram_notification("Test message")
        assert "Failed to send Telegram notification: Telegram error" in caplog.text
