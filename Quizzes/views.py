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
    """
    Creates a fresh run 'queue' and a 'fresh' list for this run.
    All questions in the new queue render as if unattempted (no pre-selected answers),
    but submitting will overwrite previous per-question answers (stats remain intact).
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    # Optional hard refresh (kept for admin/testing only)
    if request.GET.get("mode") == "all" or request.GET.get("refresh") == "1":
        # NOTE: We keep this path but the UI will no longer link to it from 'Try Again'.
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
    
    # Apply shared filters
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

    # Store in session: queue + fresh (treat as unattempted for UI)
    queue_key = f"quiz_{quiz.id}_queue"
    fresh_key = f"quiz_{quiz.id}_fresh"
    request.session[queue_key] = ids
    request.session[fresh_key] = ids[:]   # copy
    request.session.modified = True

    return redirect("Quizzes:quiz_question", quiz_id=quiz.id, question_number=1)


# ──────────────────────────────────────────────────────────────
# Quiz Complete Page
# ──────────────────────────────────────────────────────────────

@login_required
def quiz_complete(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    # Calculate based on this run's queue
    queue_key = f"quiz_{quiz.id}_queue"
    fresh_key = f"quiz_{quiz.id}_fresh"
    queue = request.session.get(queue_key, [])
    answers = attempt.extra_data.get("answers", {})

    if queue:
        total_attempted = len(queue)
        correct_in_queue = sum(
            1 for qid in queue
            if str(qid) in answers
            and isinstance(answers[str(qid)], dict)
            and answers[str(qid)].get("is_correct")
        )
    else:
        # Fallback to all answered
        total_attempted = len(answers)
        correct_in_queue = sum(
            1 for d in answers.values()
            if isinstance(d, dict) and d.get("is_correct")
        )

    percentage = round((correct_in_queue / total_attempted) * 100, 1) if total_attempted > 0 else 0

    # Save the score for reference (overall scoreboard can still use this if needed)
    attempt.score = percentage
    attempt.save()

    # Clean this run's session state
    request.session.pop(queue_key, None)
    request.session.pop(fresh_key, None)

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
    """
    Displays one question within the current quiz run.
    - Uses the queue stored in session to define this attempt's subset of questions.
    - Handles re-attempt logic (fresh questions appear unanswered but overwrite previous results).
    - Calculates accurate per-run progress (not overall quiz progress).
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    queue_key = f"quiz_{quiz.id}_queue"
    fresh_key = f"quiz_{quiz.id}_fresh"
    queue = request.session.get(queue_key, [])
    fresh_ids = set(request.session.get(fresh_key, []))

    # If queue empty, redirect to question selection
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



    # Determine if question was answered before or should appear fresh
    was_answered_before = str(question.id) in answers
    is_fresh_now = qid in fresh_ids
    already_answered = was_answered_before and not is_fresh_now
    selected_answer = None if is_fresh_now else answers.get(str(question.id), {}).get("selected")

    feedback = None


    # Check if this is the first question AND no submission has happened yet
    is_first_question = (question_number == 1)
    is_fresh_run = is_first_question and request.method != "POST"
    
    # ───────────────────────────────────────────────
    # Handle submission
    # ───────────────────────────────────────────────
    if request.method == "POST":
        selected_answer = request.POST.get("selected_choice")
        if selected_answer:
            is_correct = (selected_answer == question.correct_answer)
            answers[str(question.id)] = {"selected": selected_answer, "is_correct": is_correct}
            attempt.extra_data["answers"] = answers
            attempt.save()

            # ✅ ensure we use the latest data for recalculations
            attempt.refresh_from_db()

            feedback = "Correct!" if is_correct else "Not correct."
            already_answered = True

            # Once answered, remove from 'fresh' list so revisits show as answered
            if qid in fresh_ids:
                fresh_ids.remove(qid)
                request.session[fresh_key] = list(fresh_ids)
                request.session.modified = True

    # If user has already answered (either before or just now)
    if already_answered and feedback is None:
        feedback = "Previously attempted."

    # ───────────────────────────────────────────────
    # Calculate progress (for CURRENT RUN ONLY)
    # ───────────────────────────────────────────────
    # Refresh answers from database after potential save
    answers = attempt.extra_data.get("answers", {})

    correct_in_run = 0
    wrong_in_run = 0

    # Only count questions that have been answered AND are no longer in the fresh list
    for q in queue:
        # Skip if this question is still marked as "fresh" (not yet attempted in this run)
        if q in fresh_ids:
            continue
        
        data = answers.get(str(q))
        if isinstance(data, dict):
            if data.get("is_correct"):
                correct_in_run += 1
            else:
                wrong_in_run += 1

    attempted_in_run = correct_in_run + wrong_in_run
    unattempted_in_run = max(0, total_in_run - attempted_in_run)

    progress_correct = round((correct_in_run / total_in_run) * 100, 1) if total_in_run else 0
    progress_wrong = round((wrong_in_run / total_in_run) * 100, 1) if total_in_run else 0
    progress_attempted = round((attempted_in_run / total_in_run) * 100, 1) if total_in_run else 0
    progress_unattempted = max(0, 100 - progress_attempted)

    # ───────────────────────────────────────────────
    # Navigation + Finish state
    # ───────────────────────────────────────────────
    prev_index = question_number - 1 if question_number > 1 else None
    next_index = question_number + 1 if question_number < total_in_run else None

    is_last_question = (question_number == total_in_run)
    last_question_answered = qid not in fresh_ids and str(question.id) in answers

    # ───────────────────────────────────────────────
    # Context for template
    # ───────────────────────────────────────────────
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
        "progress_correct": progress_correct,
        "progress_wrong": progress_wrong,
        "progress_unattempted": progress_unattempted,
        "progress_attempted": progress_attempted,
        "attempted_in_run": attempted_in_run,
        "correct_in_run": correct_in_run,
        "wrong_in_run": wrong_in_run,
        "is_flagged": question.id in flagged_ids,
        "explanation": question.explanation,
        "already_answered": already_answered,
        "is_last_question": is_last_question,
        "last_question_answered": last_question_answered,
        "is_first_question": is_first_question,
        "is_fresh_run": is_fresh_run,
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







@login_required
def profile_view(request):
    """
    Displays user's overall and per-topic statistics.
    Data pulled from Attempt.extra_data['answers'] and linked quizzes.
    """
    user = request.user
    attempts = Attempt.objects.filter(user=user).select_related("quiz")

    overall_attempted = 0
    overall_correct = 0
    topic_stats = {}

    for attempt in attempts:
        answers = attempt.extra_data.get("answers", {})
        correct = sum(1 for a in answers.values() if a.get("is_correct"))
        total = len(answers)
        overall_attempted += total
        overall_correct += correct

        quiz_title = attempt.quiz.title
        if quiz_title not in topic_stats:
            topic_stats[quiz_title] = {"attempted": 0, "correct": 0}

        topic_stats[quiz_title]["attempted"] += total
        topic_stats[quiz_title]["correct"] += correct

    overall_accuracy = round((overall_correct / overall_attempted) * 100, 1) if overall_attempted else 0

    # Add percentage for each topic
    for topic, data in topic_stats.items():
        attempted = data["attempted"]
        correct = data["correct"]
        accuracy = round((correct / attempted) * 100, 1) if attempted else 0
        topic_stats[topic]["accuracy"] = accuracy

    context = {
        "overall_attempted": overall_attempted,
        "overall_correct": overall_correct,
        "overall_accuracy": overall_accuracy,
        "topic_stats": topic_stats,
    }

    return render(request, "Quizzes/profile.html", context)


def blog_view(request):
    return render(request, "Quizzes/blog.html")
