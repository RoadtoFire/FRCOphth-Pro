from typing import Set, List
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Quiz, Question, Attempt
import random


# ──────────────────────────────────────────────────────────────
# Basic static pages
# ──────────────────────────────────────────────────────────────

def about(request):
    return render(request, "Quizzes/about.html")

def terms(request):
    return render(request, "Quizzes/terms.html")

def privacy(request):
    return render(request, "Quizzes/privacy.html")


# ──────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────

def _get_attempt(user, quiz) -> Attempt:
    """Create or get an attempt with initialized JSON structure."""
    attempt, _ = Attempt.objects.get_or_create(
        user=user, quiz=quiz, defaults={"score": 0, "extra_data": {}}
    )

    if attempt.extra_data is None:
        attempt.extra_data = {}

    attempt.extra_data.setdefault("answers", {})
    attempt.extra_data.setdefault("flagged", [])
    attempt.save()
    return attempt


def _get_flag_ids(attempt: Attempt) -> Set[int]:
    return set(attempt.extra_data.get("flagged", []))


def _set_flag_ids(attempt: Attempt, ids: Set[int]) -> None:
    attempt.extra_data["flagged"] = list(ids)
    attempt.save()


def _apply_filters(qs, answers, flagged_ids, only_unattempted=False, 
                   only_wrong=False, only_flagged=False, topic=""):
    """
    Shared filter logic for both AJAX preview and start_quiz.
    Returns filtered queryset.
    """
    # Apply topic filter
    if topic:
        qs = qs.filter(category__name=topic)
    
    # Apply flag filter
    if only_flagged:
        if flagged_ids:
            qs = qs.filter(id__in=list(flagged_ids))
        else:
            qs = qs.none()  # No flagged questions = empty result
    
    # Apply unattempted filter
    if only_unattempted:
        attempted_ids = [int(qid) for qid in answers.keys()]
        if attempted_ids:
            qs = qs.exclude(id__in=attempted_ids)
    
    # Apply wrong answers filter
    if only_wrong:
        wrong_ids = [
            int(qid)
            for qid, d in answers.items()
            if isinstance(d, dict) and not d.get("is_correct")
        ]
        if wrong_ids:
            qs = qs.filter(id__in=wrong_ids)
        else:
            qs = qs.none()  # No wrong answers = empty result
    
    return qs


# ──────────────────────────────────────────────────────────────
# Home
# ──────────────────────────────────────────────────────────────

def home(request):
    quizzes = Quiz.objects.all().order_by("display_order", "title")
    return render(request, "Quizzes/home.html", {"quizzes": quizzes})


# ──────────────────────────────────────────────────────────────
# Select Questions page
# ──────────────────────────────────────────────────────────────

@login_required
def select_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    answers = attempt.extra_data.get("answers", {})
    flagged = set(attempt.extra_data.get("flagged", []))

    stats = {
        "total": quiz.questions.count(),
        "attempted": len(answers),
        "wrong": sum(
            1 for d in answers.values() if isinstance(d, dict) and not d.get("is_correct")
        ),
        "flagged": len(flagged),
        "unattempted": max(0, quiz.questions.count() - len(answers)),
    }

    topics = (
        quiz.questions.filter(category__isnull=False)
        .values_list("category__name", flat=True)
        .distinct()
        .order_by("category__name")
    )

    has_queue = bool(request.session.get(f"quiz_{quiz.id}_queue"))

    return render(
        request,
        "Quizzes/select_questions.html",
        {"quiz": quiz, "topics": topics, "stats": stats, "has_queue": has_queue},
    )


# ──────────────────────────────────────────────────────────────
# AJAX Filter Preview
# ──────────────────────────────────────────────────────────────

@login_required
def ajax_filter_preview(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    answers = attempt.extra_data.get("answers", {})
    flagged_ids = set(attempt.extra_data.get("flagged", []))

    # Get filter parameters
    only_unattempted = request.GET.get("only_unattempted") == "1"
    only_wrong = request.GET.get("only_wrong") == "1"
    only_flagged = request.GET.get("only_flagged") == "1"
    topic = request.GET.get("topic", "").strip()

    # Apply filters using shared logic
    qs = quiz.questions.all()
    qs = _apply_filters(
        qs, answers, flagged_ids,
        only_unattempted=only_unattempted,
        only_wrong=only_wrong,
        only_flagged=only_flagged,
        topic=topic
    )

    filtered_count = qs.count()

    # Calculate overall stats (not filtered)
    total = quiz.questions.count()
    attempted = len(answers)
    wrong = sum(
        1 for d in answers.values()
        if isinstance(d, dict) and not d.get("is_correct")
    )
    unattempted = max(0, total - attempted)

    data = {
        "total": total,
        "attempted": attempted,
        "wrong": wrong,
        "flagged": len(flagged_ids),
        "unattempted": unattempted,
        "filtered_count": filtered_count,
    }
    return JsonResponse(data)


# ──────────────────────────────────────────────────────────────
# Start Quiz
# ──────────────────────────────────────────────────────────────

@login_required
def start_quiz(request, quiz_id):
    """Creates or refreshes a quiz queue and redirects to question 1."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    # Refresh mode clears progress
    if request.GET.get("mode") == "all" or request.GET.get("refresh") == "1":
        attempt.extra_data = {"answers": {}, "flagged": []}
        attempt.score = 0
        attempt.save()

    answers = attempt.extra_data.get("answers", {})
    flagged_ids = set(attempt.extra_data.get("flagged", []))

    # Get filter parameters
    only_unattempted = request.GET.get("only_unattempted") == "1"
    only_wrong = request.GET.get("only_wrong") == "1"
    only_flagged = request.GET.get("only_flagged") == "1"
    topic_filter = request.GET.get("topic", "").strip()
    randomize = request.GET.get("random") == "1"

    # Start with ordered queryset
    qs = quiz.questions.all().order_by("order", "id")
    
    # Apply filters using shared logic
    qs = _apply_filters(
        qs, answers, flagged_ids,
        only_unattempted=only_unattempted,
        only_wrong=only_wrong,
        only_flagged=only_flagged,
        topic=topic_filter
    )

    # Get IDs
    ids: List[int] = list(qs.values_list("id", flat=True))

    # Check if any questions match
    if not ids:
        messages.warning(request, "No questions match your filters. Adjust filters and try again.")
        return redirect("Quizzes:select_questions", quiz.id)

    # Randomize if requested
    if randomize:
        random.shuffle(ids)

    # Store in session
    request.session[f"quiz_{quiz.id}_queue"] = ids
    request.session.modified = True

    return redirect("Quizzes:quiz_question", quiz_id=quiz.id, question_number=1)


# ──────────────────────────────────────────────────────────────
# Quiz Complete Page
# ──────────────────────────────────────────────────────────────

@login_required
def quiz_complete(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    # Get the queue to calculate based on questions attempted in this run
    queue_key = f"quiz_{quiz.id}_queue"
    queue = request.session.get(queue_key, [])
    
    answers = attempt.extra_data.get("answers", {})
    
    # Calculate stats based on the current queue (the questions in this quiz run)
    if queue:
        total_attempted = len(queue)
        attempted_in_queue = sum(1 for qid in queue if str(qid) in answers)
        correct_in_queue = sum(
            1 for qid in queue 
            if str(qid) in answers 
            and isinstance(answers[str(qid)], dict) 
            and answers[str(qid)].get("is_correct")
        )
    else:
        # Fallback to all questions if queue doesn't exist
        total_attempted = len(answers)
        correct_in_queue = sum(
            1 for d in answers.values() 
            if isinstance(d, dict) and d.get("is_correct")
        )

    # Calculate percentage
    percentage = round((correct_in_queue / total_attempted) * 100, 1) if total_attempted > 0 else 0

    # Save the score
    attempt.score = percentage
    attempt.save()

    # Clean the session queue after finishing
    request.session.pop(queue_key, None)

    context = {
        "quiz": quiz,
        "total_correct": correct_in_queue,
        "total_attempted": total_attempted,
        "percentage": percentage,
    }
    return render(request, "Quizzes/quiz_complete.html", context)


# ──────────────────────────────────────────────────────────────
# Reset Progress / Flags / Toggle Flag
# ──────────────────────────────────────────────────────────────

@login_required
def reset_progress(request, quiz_id):
    """Clears all answers and flags for the user's current attempt."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    attempt.extra_data = {"answers": {}, "flagged": []}
    attempt.score = 0
    attempt.save()

    messages.success(request, "Your quiz progress has been reset.")
    return redirect("Quizzes:select_questions", quiz.id)


@login_required
def reset_flags(request, quiz_id):
    """Clears all flagged questions for the current attempt."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    attempt.extra_data["flagged"] = []
    attempt.save()

    messages.success(request, "All flags have been removed.")
    return redirect("Quizzes:select_questions", quiz.id)


@login_required
def quiz_question(request, quiz_id, question_number):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    # Load queue
    queue_key = f"quiz_{quiz.id}_queue"
    queue: List[int] = request.session.get(queue_key, [])
    if not queue:
        messages.warning(request, "Your question queue is empty. Please start again.")
        return redirect("Quizzes:select_questions", quiz.id)

    total_in_run = len(queue)
    if question_number < 1 or question_number > total_in_run:
        return redirect("Quizzes:quiz_complete", quiz.id)

    qid = queue[question_number - 1]
    question = get_object_or_404(Question, id=qid, quiz=quiz)

    answers = attempt.extra_data.get("answers", {})
    flagged_ids = set(attempt.extra_data.get("flagged", []))

    # Check if question was already answered
    already_answered = str(question.id) in answers
    selected_answer = answers.get(str(question.id), {}).get("selected")
    
    # Handle submission: only allow if not already answered
    feedback = None
    if request.method == "POST" and not already_answered:
        selected_answer = request.POST.get("selected_choice")
        if selected_answer:
            is_correct = (selected_answer == question.correct_answer)
            answers[str(question.id)] = {"selected": selected_answer, "is_correct": is_correct}
            attempt.extra_data["answers"] = answers
            attempt.save()
            feedback = "Correct!" if is_correct else "Not correct."
            already_answered = True

    # Always show explanation if the question was ever attempted
    if already_answered:
        feedback = feedback or "Previously attempted."

    # Progress (within current run only)
    attempted_in_run = sum(1 for q in queue if str(q) in answers)
    wrong_in_run = sum(
        1 for q in queue
        if isinstance(answers.get(str(q)), dict) and not answers[str(q)].get("is_correct")
    )
    unattempted_in_run = max(0, total_in_run - attempted_in_run)

    progress_attempted = round((attempted_in_run / total_in_run) * 100, 1) if total_in_run else 0
    progress_wrong = round((wrong_in_run / total_in_run) * 100, 1) if total_in_run else 0
    progress_unattempted = max(0, 100 - progress_attempted)

    prev_index = question_number - 1 if question_number > 1 else None
    next_index = question_number + 1 if question_number < total_in_run else None

    # Check if this is the last question and if it's been answered
    is_last_question = (question_number == total_in_run)
    last_question_answered = False
    if is_last_question:
        last_question_answered = str(question.id) in answers

    context = {
        "quiz": quiz,
        "question": question,
        "question_number": question_number,
        "total_in_run": total_in_run,
        "choices": question.get_choices(),
        "selected_answer": selected_answer,
        "correct_answer": question.correct_answer,
        "feedback": feedback,
        "prev_index": prev_index,
        "next_index": next_index,
        "progress_attempted": progress_attempted,
        "progress_wrong": progress_wrong,
        "progress_unattempted": progress_unattempted,
        "is_flagged": question.id in flagged_ids,
        "explanation": question.explanation,
        "already_answered": already_answered,
        "is_last_question": is_last_question,
        "last_question_answered": last_question_answered,
    }
    return render(request, "Quizzes/quiz_question.html", context)


@login_required
def toggle_flag(request, quiz_id, question_id):
    """Toggle flag; redirect back to the current question if this isn't AJAX."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    flagged_ids = set(attempt.extra_data.get("flagged", []))
    flagged = False

    if question_id in flagged_ids:
        flagged_ids.remove(question_id)
    else:
        flagged_ids.add(question_id)
        flagged = True

    _set_flag_ids(attempt, flagged_ids)

    # AJAX? return JSON; otherwise redirect back where user was
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        return JsonResponse({"flagged": flagged})

    # Try to return user to same page gracefully
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("Quizzes:select_questions", quiz.id)