from django.contrib import admin, messages
from adminsortable2.admin import SortableAdminMixin
from django.template.response import TemplateResponse
from django.db.models import Count, Avg
from .models import Quiz, Question, Attempt, Category


class FRCOphthAdminSite(admin.AdminSite):
    site_header = "FRCOphth Dashboard"
    site_title = "FRCOphth Admin"
    index_title = "Welcome to FRCOphth Admin Panel"

    def index(self, request, extra_context=None):
        try:
            if extra_context is None:
                extra_context = {}

            total_quizzes = Quiz.objects.count()
            total_questions = Question.objects.count()
            total_categories = Category.objects.count()
            total_attempts = Attempt.objects.count()

            avg_questions_per_quiz = (
                Question.objects.values('quiz')
                .annotate(count=Count('id'))
                .aggregate(avg=Avg('count'))['avg'] or 0
            )

            # ✅ fixed related_name and potential empty cases
            top_quizzes_data = (
                Quiz.objects.annotate(num_attempts=Count('attempts', distinct=True))
                .order_by('-num_attempts')[:5]
                .values_list('title', 'num_attempts')
            )
            top_quizzes_titles = [q[0] for q in top_quizzes_data]
            top_quizzes_attempts = [q[1] for q in top_quizzes_data]

            # ✅ fixed related_name here
            category_data = (
                Category.objects.annotate(q_count=Count('questions'))
                .values_list('name', 'q_count')
            )
            category_labels = [c[0] for c in category_data]
            category_counts = [c[1] for c in category_data]

            extra_context.update({
                "total_quizzes": total_quizzes,
                "total_questions": total_questions,
                "total_categories": total_categories,
                "total_attempts": total_attempts,
                "avg_questions_per_quiz": round(avg_questions_per_quiz, 2),
                "top_quizzes_titles": top_quizzes_titles,
                "top_quizzes_attempts": top_quizzes_attempts,
                "category_labels": category_labels,
                "category_counts": category_counts,
            })

            return TemplateResponse(request, "admin/dashboard.html", extra_context)

        except Exception as e:
            print(f"[Admin Dashboard Error] {e}")
            messages.error(request, f"Error loading dashboard: {e}")
            return TemplateResponse(request, "admin/dashboard.html", {"error": str(e)})


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = (
        "order",
        "category",
        "text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "option_e",
        "correct_answer",
        "explanation",
    )
    ordering = ("order",)
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(SortableAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    inlines = [QuestionInline]

    list_display = ("title", "question_count", "unique_categories", "display_order", "created_at")
    search_fields = ("title", "questions__text")
    ordering = ("display_order", "title")
    list_display_links = ("title",)
    list_filter = ("created_at",)

    fieldsets = (
        ("Quiz Details", {
            "fields": ("title", "slug", "description", "time_limit", "image"),
            "classes": ("wide",)
        }),
        ("Display Options", {"fields": ("display_order",)}),
    )

    def unique_categories(self, obj):
        """Count distinct non-null categories."""
        return obj.questions.filter(category__isnull=False).values("category").distinct().count()
    unique_categories.short_description = "Categories"


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("name", "display_order")
    ordering = ("display_order",)
    search_fields = ("name",)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "score", "started_at")
    search_fields = ("user__username", "quiz__title")
    list_filter = ("quiz", "started_at")
