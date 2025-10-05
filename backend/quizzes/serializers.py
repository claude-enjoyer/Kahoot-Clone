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
    index = serializers.IntegerField(required=False)
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

        # Check for duplicate question indices
        indices = [
            question.get("index")
            for question in data["questions"]
            if question.get("index") is not None
        ]
        if len(indices) != len(set(indices)):
            raise serializers.ValidationError("Duplicate question indices are not allowed.")
        return data
