from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Quiz


@patch("django_elasticsearch_dsl.registries.registry.delete")
@patch("django_elasticsearch_dsl.registries.registry.update")
class QuizAPITests(APITestCase):
    def setUp(self):
        """Set up users and base data for tests."""
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self.list_create_url = reverse("quiz-list")
        self.valid_quiz_data = {
            "name": "Valid Quiz",
            "questions": [
                {
                    "body": "Valid Question?",
                    "answers": [{"body": "a"}, {"body": "b"}, {"body": "c"}, {"body": "d"}],
                    "correct_answer": 4,
                }
            ],
        }

    def detail_url(self, slug):
        """Return the detail URL for a given slug."""
        return reverse("quiz-detail", kwargs={"slug": slug})

    def test_create_quiz_success(self, mock_update, mock_delete):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_quiz_unauthenticated(self, mock_update, mock_delete):
        response = self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_quizzes_authenticated(self, mock_update, mock_delete):
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        self.client.force_authenticate(user=self.user2)
        self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_own_quiz(self, mock_update, mock_delete):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        quiz_slug = response.data["slug"]
        url = self.detail_url(quiz_slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_other_user_quiz_fails(self, mock_update, mock_delete):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        quiz_slug = response.data["slug"]
        url = self.detail_url(quiz_slug)
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_quiz(self, mock_update, mock_delete):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        quiz_slug = response.data["slug"]
        url = self.detail_url(quiz_slug)
        updated_data = self.valid_quiz_data.copy()
        updated_data["name"] = "Updated Name"
        response = self.client.put(url, updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_other_user_quiz_fails(self, mock_update, mock_delete):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        quiz_slug = response.data["slug"]
        url = self.detail_url(quiz_slug)
        self.client.force_authenticate(user=self.user2)
        response = self.client.put(url, self.valid_quiz_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_quiz(self, mock_update, mock_delete):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        quiz_slug = response.data["slug"]
        url = self.detail_url(quiz_slug)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_user_quiz_fails(self, mock_update, mock_delete):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_create_url, self.valid_quiz_data, format="json")
        quiz_slug = response.data["slug"]
        url = self.detail_url(quiz_slug)
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)