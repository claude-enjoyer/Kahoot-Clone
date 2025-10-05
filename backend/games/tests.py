import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from django.utils import timezone

from quizzes.models import Answer, Question, Quiz

from .models import Game, Player, initialize_game, initialize_player


class GameAndPlayerModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up class-level patches and signal disconnections."""
        super().setUpClass()
        cls.patcher_update = patch("django_elasticsearch_dsl.registries.registry.update")
        cls.mock_update = cls.patcher_update.start()
        cls.patcher_delete = patch("django_elasticsearch_dsl.registries.registry.delete")
        cls.mock_delete = cls.patcher_delete.start()
        post_save.disconnect(initialize_game, sender=Game)
        post_save.disconnect(initialize_player, sender=Player)

    @classmethod
    def tearDownClass(cls):
        """Tear down class-level patches and reconnect signals."""
        super().tearDownClass()
        cls.patcher_update.stop()
        cls.patcher_delete.stop()
        post_save.connect(initialize_game, sender=Game)
        post_save.connect(initialize_player, sender=Player)

    def setUp(self):
        """Set up data for each test."""
        self.user = User.objects.create_user(
            username=f"user_{uuid.uuid4().hex}", password="testpassword"
        )
        quiz = Quiz.objects.create(name="Test Quiz", creator=self.user)
        self.question1 = Question.objects.create(
            quiz=quiz, body="Q1", index=1, correct_answer=1
        )
        self.question2 = Question.objects.create(
            quiz=quiz, body="Q2", index=2, correct_answer=2
        )
        Answer.objects.create(question=self.question1, body="A1")
        Answer.objects.create(question=self.question2, body="A1")

        # Fetch a fresh quiz instance with pre-fetched questions
        self.quiz = Quiz.objects.prefetch_related('questions').get(pk=quiz.pk)

        self.game = Game.objects.create(
            creator=self.user, quiz=self.quiz, slug=uuid.uuid4().hex[:5]
        )
        self.game.current_question = self.question1
        self.game.save()

    def test_advance_game(self):
        """Test that advance_game moves to the next question."""
        result = self.game.advance_game()
        self.assertTrue(result)
        reloaded_game = Game.objects.get(pk=self.game.pk)
        self.assertEqual(reloaded_game.current_question, self.question2)

    def test_advance_game_completes_at_end(self):
        """Test that advance_game completes the game after the last question."""
        self.game.current_question = self.question2
        self.game.save()
        result = self.game.advance_game()
        self.assertFalse(result)
        reloaded_game = Game.objects.get(pk=self.game.pk)
        self.assertEqual(reloaded_game.state, "complete")

    def test_get_leaderboard(self):
        """Test that the leaderboard is correctly generated and sorted."""
        Player.objects.create(
            game=self.game, email="p2@test.com", slug=uuid.uuid4().hex,
            answers="1,1", answer_bonus="50,20"
        )
        Player.objects.create(
            game=self.game, email="p1@test.com", slug=uuid.uuid4().hex,
            answers="1,2", answer_bonus="10,80"
        )
        leaderboard = self.game.get_leaderboard()
        expected = {"p1@test.com": 290, "p2@test.com": 170}
        self.assertEqual(leaderboard, expected)

    def test_player_score(self):
        """Test that a player's score is calculated correctly."""
        player = Player.objects.create(
            game=self.game, email="p@test.com", slug=uuid.uuid4().hex,
            answers="1,2", answer_bonus="10,80"
        )
        self.assertEqual(player.get_score(), 290)

    def test_set_player_answer(self):
        """Test setting a player's answer and bonus calculation."""
        player = Player.objects.create(
            game=self.game, email="p@test.com", slug=uuid.uuid4().hex,
            answers="0,0", answer_bonus="0,0"
        )
        player.set_answer(1, 1)
        self.assertEqual(player.get_answer(1), 1)
        self.game.timer = timezone.now() - timezone.timedelta(seconds=10)
        self.game.save()
        player.set_answer(2, 2)
        bonuses = player.answer_bonus.split(",")
        self.assertEqual(int(bonuses[1]), 90)