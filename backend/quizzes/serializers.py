from rest_framework import serializers
from .models import Quiz, Question, Answer

from drf_writable_nested.serializers import WritableNestedModelSerializer


class AnswerSerializer(WritableNestedModelSerializer):
    index = serializers.IntegerField(read_only=True)

    class Meta:
        model = Answer
        fields = (
            "body",
            "index",
        )


class QuestionSerializer(WritableNestedModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = (
            "body",
            "answers",
            "correct_answer",
            "index",
        )

    def validate(self, data):
        if len(data["answers"]) != 4:
            raise serializers.ValidationError(
                "Must be exactly 4 answers to each question"
            )
        return data


class QuizSerializer(WritableNestedModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = (
            "slug",
            "name",
            "questions",
        )
        lookup_field = "slug"
        depth = 2

    def validate(self, data):
        if len(data["questions"]) == 0:
            raise serializers.ValidationError("Must be at least one question")
        if len(data["questions"]) > 50:
            raise serializers.ValidationError("Can not have more than 50 questions")

        question_indices = [question["index"] for question in data["questions"]]
        if len(question_indices) != len(set(question_indices)):
            raise serializers.ValidationError("Question indices must be unique")

        return data
