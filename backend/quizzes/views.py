from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Quiz, Question, Answer
from .serializers import QuizSerializer, QuestionSerializer, AnswerSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from elasticsearch_dsl import Q
from .documents import QuizDocument
from .serializers import QuizSerializer


class PaginatedElasticSearchAPIView(APIView):
    serializer_class = None
    document_class = None

    def get(self, request, *args, **kwargs):
        # Get the current user from the request
        user = self.request.user
        # Filter the queryset to only include quizzes created by the current user
        # queryset = queryset.filter("term", creator__username=user.username)
        # return queryset
        query = request.GET.get("q")
        search = self.document_class.search().query(
            "multi_match",
            query=query,
            fields=["name", "questions.body", "questions.answers.body"],
        )
        search = search.filter("term", creator__username=user.username)
        response = search.execute()

        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_results = paginator.paginate_queryset(response.hits, request)
        serializer = self.serializer_class(paginated_results, many=True)
        return paginator.get_paginated_response(serializer.data)


class QuizSearchView(PaginatedElasticSearchAPIView):
    serializer_class = QuizSerializer
    document_class = QuizDocument


class QuizView(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    lookup_field = "slug"
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get_queryset(self):
        return super(QuizView, self).get_queryset().filter(creator=self.request.user)
