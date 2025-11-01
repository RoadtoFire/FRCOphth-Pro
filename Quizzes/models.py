from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field



# ---------------------------
# Category
# ---------------------------
class Category(models.Model):
    """
    Represents a subject area or grouping of questions.
    e.g. Anatomy, Pathology, Optics.
    """
    name = models.CharField(max_length=200, unique=True)
    display_order = models.PositiveIntegerField(default=0)  # ✅ added for homepage order

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


# ---------------------------
# Quiz
# ---------------------------
class Quiz(models.Model):
    """
    A quiz is a collection of questions.
    Each quiz has its own description and display order.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    time_limit = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to="quiz_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ["display_order", "-title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def question_count(self):
        """Count of questions in this quiz."""
        return self.questions.count()


# ---------------------------
# Question
# ---------------------------
class Question(models.Model):
    """
    Each question belongs to exactly one quiz and one category.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    category = models.ForeignKey(
        Category, related_name="questions", on_delete=models.SET_NULL, null=True, blank=True
    )  # ✅ added related_name

    text = models.TextField()

    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    option_e = models.CharField(max_length=300)

    correct_answer = models.CharField(
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E")],
        default="A",
    )
    explanation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.quiz.title} - {self.text[:50]}"

    def get_choices(self):
        return [
            ("A", self.option_a),
            ("B", self.option_b),
            ("C", self.option_c),
            ("D", self.option_d),
            ("E", self.option_e),
        ]


# ---------------------------
# Attempt
# ---------------------------
class Attempt(models.Model):
    """
    Tracks each user's attempt per quiz and question set.
    Stores answers and flags inside a JSONField (extra_data).
    """
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    quiz = models.ForeignKey(Quiz, related_name="attempts", on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question, related_name="attempts", on_delete=models.CASCADE, null=True, blank=True
    )

    selected_option = models.CharField(
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E")],
        null=True,
        blank=True,
    )
    is_correct = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    score = models.FloatField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    extra_data = models.JSONField(default=dict, blank=True)  # ✅ Added JSON storage

    class Meta:
        verbose_name_plural = "Attempts"

    def __str__(self):
        return f"{self.user} - {self.quiz.title}"


from django_ckeditor_5.fields import CKEditor5Field

from django.utils.text import slugify
from django.contrib.auth.models import User

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    thumbnail = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    short_description = models.TextField(max_length=300, help_text="Shown on the blog homepage.")
    content = CKEditor5Field(config_name='default')
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    


class AIQuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_quiz_attempts")
    score = models.FloatField()  # percentage
    total_questions = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.score}% ({self.total_questions}Qs)"