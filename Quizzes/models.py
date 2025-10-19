from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    time_limit = models.PositiveIntegerField(null=True, blank=True)  # in minutes (optional)
    image = models.ImageField(upload_to="quiz_images/", null=True, blank=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ["display_order", '-title']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    topic_name = models.CharField(max_length=200)  # For filtering & random quizzes
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


class Attempt(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    quiz = models.ForeignKey(Quiz, related_name="attempts", on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)  # stores answers, flags, etc.

    def __str__(self):
        return f"Attempt by {self.user} on {self.quiz}"


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('3-month', '3-Month Plan'),
        ('6-month', '6-Month Plan'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    active = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"
