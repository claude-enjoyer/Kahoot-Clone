from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import Quiz


class QuizPostTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user1.set_password("password")
        self.user1.save()

    def test_post_quiz_with_no_questions(self):
        """
        If a quiz has no questions, it should fail validation
        """
        url = reverse("quiz-list")
        data = {"name": "A quiz with no questions", "questions": []}
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, data, format="json")
        self.client.force_authenticate(user=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"non_field_errors": ["Must be at least one question"]}
        )

    def test_post_quiz_with_4_answers(self):
        """
        If a quiz has a question with 4 answers, it should pass validation
        """
        url = reverse("quiz-list")
        data = {
            "name": "Valid Quiz",
            "questions": [
                {
                    "body": "Valid Question?",
                    "answers": [
                        {"body": "a"},
                        {"body": "b"},
                        {"body": "c"},
                        {"body": "d"},
                    ],
                    "correct_answer": 4,
                    "index": 1,
                }
            ],
        }
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, data, format="json")
        self.client.force_authenticate(user=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_quiz_with_3_answers(self):
        """
        If a quiz has a question with 3 answers, it should fail validation
        """
        url = reverse("quiz-list")
        data = {
            "name": "Invalid Quiz",
            "questions": [
                {
                    "body": "Invalid Question?",
                    "answers": [
                        {"body": "a"},
                        {"body": "b"},
                        {"body": "c"},
                    ],
                    "correct_answer": 4,
                    "index": 1,
                }
            ],
        }
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, data, format="json")
        self.client.force_authenticate(user=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "questions": [
                    {"non_field_errors": ["Must be exactly 4 answers to each question"]}
                ]
            },
        )

    def test_post_quiz_with_5_answers(self):
        """
        If a quiz has a question with 5 answers, it should fail validation
        """
        url = reverse("quiz-list")
        data = {
            "name": "Invalid Quiz",
            "questions": [
                {
                    "body": "Invalid Question?",
                    "answers": [
                        {"body": "a"},
                        {"body": "b"},
                        {"body": "c"},
                        {"body": "d"},
                        {"body": "e"},
                    ],
                    "correct_answer": 4,
                    "index": 1,
                }
            ],
        }
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, data, format="json")
        self.client.force_authenticate(user=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "questions": [
                    {"non_field_errors": ["Must be exactly 4 answers to each question"]}
                ]
            },
        )

    def test_post_quiz_with_empty_name(self):
        """
        If a quiz has an empty name, it should fail validation
        """
        url = reverse("quiz-list")
        data = {
            "name": "",
            "questions": [
                {
                    "body": "Valid Question?",
                    "answers": [
                        {"body": "a"},
                        {"body": "b"},
                        {"body": "c"},
                        {"body": "d"},
                    ],
                    "correct_answer": 1,
                    "index": 1,
                }
            ],
        }
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, data, format="json")
        self.client.force_authenticate(user=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_post_quiz_with_duplicate_question_indices(self):
        """
        If a quiz has questions with duplicate indices, it should fail validation
        """
        url = reverse("quiz-list")
        data = {
            "name": "Quiz with duplicate questions",
            "questions": [
                {
                    "body": "Question 1?",
                    "answers": [
                        {"body": "a"},
                        {"body": "b"},
                        {"body": "c"},
                        {"body": "d"},
                    ],
                    "correct_answer": 1,
                    "index": 1,
                },
                {
                    "body": "Question 2?",
                    "answers": [
                        {"body": "a"},
                        {"body": "b"},
                        {"body": "c"},
                        {"body": "d"},
                    ],
                    "correct_answer": 2,
                    "index": 1,  # Duplicate index
                },
            ],
        }
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, data, format="json")
        self.client.force_authenticate(user=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
