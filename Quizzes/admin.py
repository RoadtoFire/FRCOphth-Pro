from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
from .models import Quiz, Question, Attempt, Subscription


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = (
        "order",
        "text",
        "topic_name",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "option_e",
        "correct_answer",
        "explanation",
    )


@admin.register(Quiz)
class QuizAdmin(SortableAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    inlines = [QuestionInline]

    # Include display_order + keep your existing fields
    list_display = ("title", "category", "display_order", "created_at")
    list_editable = ()
    search_fields = ("title", "questions__text")
    ordering = ("display_order", "title")  # Sort by display_order first, then title

    list_display_links = ("title",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order", "topic_name", "short_text")
    search_fields = ("text", "topic_name")
    list_filter = ("quiz", "topic_name")

    def short_text(self, obj):
        return obj.text[:60]
    short_text.short_description = "Question"


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz", "score", "started_at", "finished_at")
    readonly_fields = ("started_at", "finished_at", "score", "extra_data")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "active", "start_date", "end_date")
    list_filter = ("active", "plan")
