from django.utils import timezone
import uuid
import ast

from django.contrib.auth.models import User
from django.core.validators import validate_comma_separated_integer_list
from django.dispatch import receiver

from quizzes.models import Quiz, Question, Answer
from django_fsm import FSMField, transition

from django.db import models


class Game(models.Model):
    creator = models.ForeignKey(
        User,
        related_name="games",
        on_delete=models.CASCADE,
    )
    quiz = models.ForeignKey(
        Quiz,
        null=False,
        on_delete=models.CASCADE,
    )
    current_question = models.ForeignKey(
        Question, null=True, related_name="game", on_delete=models.CASCADE
    )
    state = FSMField(default="active", protected=True)
    slug = models.CharField(unique=True, max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now_add=False, null=True)
    timer = models.DateTimeField(auto_now_add=False, null=True)

    # advance the game forward one question, return false if the game is ove
    def advance_game(self):
        if self.current_question.index < self.quiz.questions.count():
            self.current_question = self.quiz.questions.get(
                index=self.current_question.index + 1
            )
            self.timer = None
            self.save()
            return True
        self.to_state_complete()
        self.save()
        return False

    # return a sorted dict of players and their scores
    def get_leaderboard(self):
        leaderboard = {}
        for player in self.players.all():
            leaderboard[player.email] = player.get_score()

        return {
            k: v
            for k, v in sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        }

    # return an object for use with rechart
    def get_rechart_object(self):
        obj = []
        for player in self.players.all():
            obj.append(player.get_recharts_object())
        return obj

    # precondition for state transition, make sure we are on the last question before we finish the game
    def can_complete(self):
        return not self.current_question.index < self.quiz.questions.count()

    # complete the game
    @transition(
        field=state, source="active", target="complete", conditions=[can_complete]
    )
    def to_state_complete(self):
        self.current_question = None
        self.slug = uuid.uuid4().hex[:6].upper()
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.creator.username}: {self.quiz.name}"


# runs after a Game is saved to DB, set current question to the first question if the game is just starting
@receiver(models.signals.post_save, sender=Game)
def initialize_game(sender, instance, created, *args, **kwargs):
    if created:
        if not instance.current_question and instance.state == "active":
            instance.current_question = instance.quiz.questions.get(index=1)
            instance.save()


class Player(models.Model):
    email = models.EmailField()
    game = models.ForeignKey(
        Game,
        null=False,
        related_name="players",
        on_delete=models.CASCADE,
    )
    slug = models.CharField(unique=True, max_length=5)
    name = models.CharField(max_length=30, default=None, null=True)
    answers = models.CharField(
        validators=[validate_comma_separated_integer_list], max_length=100
    )  # 100 chars, enough for 50 comma seperated answers
    answer_bonus = models.CharField(
        validators=[validate_comma_separated_integer_list], max_length=300
    )

    # helper functions to convert between string and list
    def set_answer(self, question_index, answer):
        questions = self.game.quiz.questions
        if question_index < 1 or question_index > questions.count():
            raise ValueError(
                f"get_answer: question_index should be between 1 and {questions.count()}, got {question_index}"
            )
        if int(answer) < 1 or int(answer) > 4:
            raise ValueError(
                f"set_answer: question_index should be between 1 and 4, got {answer}"
            )
        answers = ast.literal_eval(f"[{self.answers}]")
        if answer == answers[question_index - 1]:
            return
        bonus = ast.literal_eval(f"[{self.answer_bonus}]")
        answers[question_index - 1] = answer
        correct_answers = {q.index: q.correct_answer for q in questions.all()}
        if correct_answers.get(question_index) == answer:
            if not self.game.timer:
                self.game.timer = timezone.now()
                bonus[question_index - 1] = 100
            else:
                bonus[question_index - 1] = max(
                    0, 100 - int((timezone.now() - self.game.timer).seconds)
                )
        else:
            bonus[question_index - 1] = 0
        self.answers = ",".join([str(i) for i in answers])
        self.answer_bonus = ",".join([str(i) for i in bonus])
        self.save()

    def get_answer_list(self):
        return ast.literal_eval(f"[{self.answers}]")

    def get_answer(self, question_index):
        if question_index < 1 or question_index > self.game.quiz.questions.count():
            raise ValueError(
                f"get_answer: question_index should be between 1 and {self.game.quiz.questions.count()}, got {question_index}"
            )
        return self.get_answer_list()[question_index - 1]

    def num_correct_answers(self):
        correct = 0
        answers = self.get_answer_list()
        # Create a dictionary of correct answers for efficient lookup
        correct_answers = {
            q.index: q.correct_answer for q in self.game.quiz.questions.all()
        }
        for i, player_answer in enumerate(answers):
            if player_answer == correct_answers.get(i + 1):
                correct += 1
        return correct

    # check if player got a given question correct
    def question_correct(self, question_index):
        # Create a dictionary of correct answers for efficient lookup
        correct_answers = {
            q.index: q.correct_answer for q in self.game.quiz.questions.all()
        }
        return self.get_answer(question_index) == correct_answers.get(question_index)

    # check if player got the previous question correct
    def previous_question_correct(self):
        if self.game.state == "complete":
            return self.question_correct(self.game.quiz.questions.count())
        return self.question_correct(self.game.current_question.index - 1)

    def total_bonus(self):
        bonus = 0
        bonus_list = ast.literal_eval(f"[{self.answer_bonus}]")
        quiz = self.game.quiz
        for i in range(0, quiz.questions.count()):
            bonus += bonus_list[i]
        return bonus

    # return the player's score - for now just the number of correct answers
    def get_score(self):
        return (self.num_correct_answers() * 100) + (self.total_bonus())

    # return an object for use with rechart
    def get_recharts_object(self):
        return {
            "name": self.name if self.name else self.email,
            "value": self.get_score(),
        }

    def __str__(self):
        return f"{self.email}: {self.game.quiz.name}"


# runs after a player is saved to DB, make sure they have an initialized answer list and id
@receiver(models.signals.post_save, sender=Player)
def initialize_player(sender, instance, created, *args, **kwargs):
    if created:
        if not instance.slug:
            slug = uuid.uuid4().hex[:6].upper()
            while Player.objects.filter(slug=slug).exists():
                slug = uuid.uuid4().hex[:6].upper()
            instance.slug = slug
        if not instance.answers:
            send_email_task(instance)
            instance.answers = ",".join(
                [str(0) for i in range(0, instance.game.quiz.questions.count())]
            )
            instance.answer_bonus = ",".join(
                [str(0) for i in range(0, instance.game.quiz.questions.count())]
            )
        instance.save()
