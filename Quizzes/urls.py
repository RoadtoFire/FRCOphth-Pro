from django.urls import path
from . import views

app_name = "Quizzes"

urlpatterns = [

     # Home (after login): list of quizzes
    path("", views.home, name="home"),

    path("<int:quiz_id>/start/", views.start_quiz, name="start_quiz"),
    path("<int:quiz_id>/question/<int:question_number>/", views.quiz_question, name="quiz_question"),
    path("<int:quiz_id>/complete/", views.quiz_complete, name="quiz_complete"),
    path("<int:quiz_id>/select/", views.select_questions, name="select_questions"),
    path("<int:quiz_id>/reset_progress/", views.reset_progress, name="reset_progress"),
    path("<int:quiz_id>/reset_flags/", views.reset_flags, name="reset_flags"),
    path("<int:quiz_id>/question/<int:question_id>/flag/", views.toggle_flag, name="toggle_flag"),
    path('<int:quiz_id>/ajax-filter-preview/', views.ajax_filter_preview, name='ajax_filter_preview'),
    path("about/", views.about, name="about"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
    path("profile/", views.profile_view, name="profile"),


    path("ai-quiz/", views.ai_quiz_select_view, name="ai_quiz_select"),
    path("ai-quiz/start/", views.ai_quiz_start_view, name="ai_quiz_start"),
    path("ai-quiz/question/<int:question_number>/", views.ai_quiz_question_view, name="ai_quiz_question"),
    path("ai-quiz/complete/", views.ai_quiz_complete_view, name="ai_quiz_complete"),

    path("blog/", views.blog_index, name="blog_index"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),


]
