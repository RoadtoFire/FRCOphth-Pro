from typing import Set, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Quiz, Question, Attempt

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def about(request):
    return render(request, "Quizzes/about.html")

def terms(request):
    return render(request, "Quizzes/terms.html")

def privacy(request):
    return render(request, "Quizzes/privacy.html")





def _get_attempt(user, quiz) -> Attempt:
    """
    Return/create Attempt with guaranteed structure:
      extra_data = {
        "answers": { "<qid>": {"selected": "A/B/C/D", "is_correct": bool}, ... },
        "flagged": [<qid>, ...]
      }
    """
    attempt, _ = Attempt.objects.get_or_create(
        user=user,
        quiz=quiz,
        defaults={"score": 0, "extra_data": {}},
    )
    if attempt.extra_data is None:
        attempt.extra_data = {}

    if "answers" not in attempt.extra_data or not isinstance(attempt.extra_data["answers"], dict):
        attempt.extra_data["answers"] = {}

    if "flagged" not in attempt.extra_data or not isinstance(attempt.extra_data["flagged"], list):
        attempt.extra_data["flagged"] = []

    attempt.save()
    return attempt


def _get_flag_ids(attempt: Attempt) -> Set[int]:
    return set(attempt.extra_data.get("flagged", []))


def _set_flag_ids(attempt: Attempt, ids: Set[int]) -> None:
    attempt.extra_data["flagged"] = list(ids)
    attempt.save()


# ──────────────────────────────────────────────────────────────────────────────
# Public landing / list
# ──────────────────────────────────────────────────────────────────────────────

def home(request):
    quizzes = Quiz.objects.all().order_by("display_order", "title")
    return render(request, "Quizzes/home.html", {"quizzes": quizzes})


# ──────────────────────────────────────────────────────────────────────────────
# Select Questions page (AJAX preview + Start)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def select_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    answers = attempt.extra_data.get("answers", {})
    flagged = set(attempt.extra_data.get("flagged", []))

    stats = {
        "total": quiz.questions.count(),
        "attempted": len(answers),
        "wrong": sum(1 for d in answers.values() if isinstance(d, dict) and not d.get("is_correct")),
        "flagged": len(flagged),
        "unattempted": max(0, quiz.questions.count() - len(answers)),
        "last_finished": None,  # add if you store it
        "last_score": None,     # add if you store it
    }

    topics = quiz.questions.values_list("topic_name", flat=True).distinct().order_by("topic_name")

    # Did the user already build a queue?
    has_queue = bool(request.session.get(f"quiz_{quiz.id}_queue"))

    return render(
        request,
        "Quizzes/select_questions.html",
        {
            "quiz": quiz,
            "topics": topics,
            "stats": stats,
            "has_queue": has_queue,
        },
    )


@login_required
def ajax_filter_preview(request, quiz_id):
    """Live preview for counts + progress. Always ensures Attempt exists."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    answers = attempt.extra_data.get("answers", {})
    flagged_ids = set(attempt.extra_data.get("flagged", []))

    # Read filters
    only_unattempted = request.GET.get("only_unattempted") == "1"
    only_wrong = request.GET.get("only_wrong") == "1"
    only_flagged = request.GET.get("only_flagged") == "1"
    topic = request.GET.get("topic", "").strip()

    qs = quiz.questions.all()
    if topic:
        qs = qs.filter(topic_name=topic)
    if only_flagged:
        qs = qs.filter(id__in=list(flagged_ids))
    if only_unattempted:
        attempted_ids = [int(qid) for qid in answers.keys()]
        if attempted_ids:
            qs = qs.exclude(id__in=attempted_ids)
    if only_wrong:
        wrong_ids = [int(qid) for qid, d in answers.items() if isinstance(d, dict) and not d.get("is_correct")]
        if wrong_ids:
            qs = qs.filter(id__in=wrong_ids)

    total = quiz.questions.count()
    attempted = len(answers)
    wrong = sum(1 for d in answers.values() if isinstance(d, dict) and not d.get("is_correct"))
    flagged_count = len(flagged_ids)
    unattempted = max(0, total - attempted)
    filtered_count = qs.count()

    return JsonResponse(
        {
            "total": total,
            "attempted": attempted,
            "wrong": wrong,
            "flagged": flagged_count,
            "unattempted": unattempted,
            "filtered_count": filtered_count,
        }
    )


@login_required
def start_quiz(request, quiz_id):
    """Create queue from filters, optionally reset attempt, then go to Q1."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    # If reattempting (from complete page / force fresh):
    if request.GET.get("mode") == "all" or request.GET.get("refresh") == "1":
        attempt.extra_data["answers"] = {}
        attempt.extra_data["flagged"] = []
        attempt.score = 0
        attempt.save()

    answers = attempt.extra_data.get("answers", {})
    flagged_ids = set(attempt.extra_data.get("flagged", []))

    # Filters
    only_unattempted_param = request.GET.get("only_unattempted")
    only_flagged_param = request.GET.get("only_flagged")
    only_wrong_param = request.GET.get("only_wrong")
    topic_filter = request.GET.get("topic", "")
    randomize = request.GET.get("random") == "1"

    # Default unattempted ON only when absolutely no params provided
    if all(param is None for param in [only_unattempted_param, only_flagged_param, only_wrong_param, topic_filter, request.GET.get("random")]):
        only_unattempted = True
    else:
        only_unattempted = (only_unattempted_param == "1")

    only_wrong = (only_wrong_param == "1")
    only_flagged = (only_flagged_param == "1")

    # Build queryset
    qs = quiz.questions.all().order_by("order", "id")
    if topic_filter:
        qs = qs.filter(topic_name=topic_filter)
    if only_flagged:
        qs = qs.filter(id__in=list(flagged_ids))
    if only_unattempted:
        attempted_ids = [int(qid) for qid in answers.keys()]
        if attempted_ids:
            qs = qs.exclude(id__in=attempted_ids)
    if only_wrong:
        wrong_ids = [int(qid) for qid, d in answers.items() if isinstance(d, dict) and not d.get("is_correct")]
        if wrong_ids:
            qs = qs.filter(id__in=wrong_ids)

    ids: List[int] = list(qs.values_list("id", flat=True))

    if not ids:
        messages.warning(request, "No questions match your filters. Adjust filters and try again.")
        return redirect("Quizzes:select_questions", quiz_id=quiz.id)

    # Randomize order if requested
    if randomize:
        import random
        random.shuffle(ids)

    # Seed session queue + progress (progress is per-run)
    request.session[f"quiz_{quiz.id}_queue"] = ids
    request.session[f"quiz_{quiz.id}_progress"] = {"correct": 0, "attempted": 0, "total": len(ids)}
    request.session.modified = True

    return redirect("Quizzes:quiz_question", quiz_id=quiz.id, question_number=1)


# ──────────────────────────────────────────────────────────────────────────────
# Toggle flag (AJAX or fallback)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def toggle_flag(request, quiz_id, question_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    attempt = _get_attempt(request.user, quiz)

    flags = set(attempt.extra_data.get("flagged", []))

    if request.method == "POST":
        if question.id in flags:
            flags.remove(question.id)
            flagged = False
        else:
            flags.add(question.id)
            flagged = True

        _set_flag_ids(attempt, flags)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"flagged": flagged, "status": "ok"})

    return redirect(request.META.get("HTTP_REFERER", "Quizzes:select_questions"))


# ──────────────────────────────────────────────────────────────────────────────
# Question runner (uses queue in session)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def quiz_question(request, quiz_id, question_number: int):
    """
    Renders the Nth question in the current session queue.
    Saves answers as dicts with is_correct.
    Supports Previous/Next navigation by index.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)

    queue_key = f"quiz_{quiz.id}_queue"
    progress_key = f"quiz_{quiz.id}_progress"
    queue = request.session.get(queue_key)

    # If no queue, start a default run of all questions in order.
    if not queue:
        queue = list(quiz.questions.order_by("order", "id").values_list("id", flat=True))
        request.session[queue_key] = queue
        request.session[progress_key] = {"correct": 0, "attempted": 0, "total": len(queue)}
        request.session.modified = True

    # question_number is 1-based index into the queue
    idx = max(1, min(int(question_number), len(queue))) - 1
    qid = queue[idx]
    question = get_object_or_404(Question, id=qid, quiz=quiz)

    attempt = _get_attempt(request.user, quiz)
    data = attempt.extra_data or {}
    answers = data.get("answers", {})
    flagged_ids = set(data.get("flagged", []))

    selected_answer = None
    feedback = None
    correct_answer = question.correct_answer

    # Handle submission
    if request.method == "POST":
        selected = request.POST.get("selected_choice")
        if selected:
            is_correct = (selected == correct_answer)
            answers[str(question.id)] = {"selected": selected, "is_correct": is_correct}
            data["answers"] = answers
            attempt.extra_data = data
            attempt.save()

            # Update run progress (session)
            prog = request.session.get(progress_key, {"correct": 0, "attempted": 0, "total": len(queue)})
            prog["attempted"] = len(answers)
            prog["correct"] = sum(1 for d in answers.values() if isinstance(d, dict) and d.get("is_correct"))
            request.session[progress_key] = prog
            request.session.modified = True

            feedback = "Correct!" if is_correct else "Incorrect!"
            selected_answer = selected

    else:
        # If already answered, preload selection & feedback
        prev = answers.get(str(question.id))
        if isinstance(prev, dict):
            selected_answer = prev.get("selected")
            feedback = "Correct!" if prev.get("is_correct") else "Incorrect!"

    prev_index = idx - 1 if idx > 0 else None
    next_index = idx + 1 if idx < (len(queue) - 1) else None

    # ✅ Calculate progress bar percentages
    total_questions = len(queue)
    attempted = len([a for a in answers.values() if isinstance(a, dict)])
    wrong = len([a for a in answers.values() if isinstance(a, dict) and not a.get("is_correct")])
    unattempted = max(total_questions - attempted, 0)

    if total_questions > 0:
        progress_attempted = int((attempted / total_questions) * 100)
        progress_wrong = int((wrong / total_questions) * 100)
        progress_unattempted = 100 - progress_attempted - progress_wrong
    else:
        progress_attempted = progress_wrong = progress_unattempted = 0

    context = {
        "quiz": quiz,
        "question": question,
        "choices": question.get_choices(),
        "question_number": idx + 1,
        "total_in_run": len(queue),
        "prev_index": prev_index + 1 if prev_index is not None else None,
        "next_index": next_index + 1 if next_index is not None else None,
        "selected_answer": selected_answer,
        "correct_answer": correct_answer,
        "feedback": feedback,
        "is_flagged": question.id in flagged_ids,
        # ✅ Added for progress bars
        "progress_attempted": progress_attempted,
        "progress_wrong": progress_wrong,
        "progress_unattempted": progress_unattempted,
    }

    return render(request, "Quizzes/quiz_question.html", context)



# ──────────────────────────────────────────────────────────────────────────────
# Completion
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def quiz_complete(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)

    answers = attempt.extra_data.get("answers", {})
    # supports both dict-style (new) and legacy string-style (old)
    total_attempted = len(answers)
    total_correct = 0
    for a in answers.values():
        if isinstance(a, dict):
            if a.get("is_correct"):
                total_correct += 1

    percentage = round((total_correct / total_attempted) * 100, 1) if total_attempted else 0

    # clear run queue/progress so reattempt is clean
    request.session.pop(f"quiz_{quiz.id}_queue", None)
    request.session.pop(f"quiz_{quiz.id}_progress", None)
    request.session.modified = True

    return render(
        request,
        "Quizzes/quiz_complete.html",
        {
            "quiz": quiz,
            "total_correct": total_correct,
            "total_attempted": total_attempted,
            "percentage": percentage,
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# Resets
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def reset_progress(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)
    attempt.extra_data["answers"] = {}
    attempt.score = 0
    attempt.save()
    request.session.pop(f"quiz_{quiz.id}_queue", None)
    request.session.pop(f"quiz_{quiz.id}_progress", None)
    request.session.modified = True
    messages.success(request, "Progress reset.")
    return redirect("Quizzes:select_questions", quiz_id=quiz.id)


@login_required
def reset_flags(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = _get_attempt(request.user, quiz)
    _set_flag_ids(attempt, set())
    request.session.pop(f"quiz_{quiz.id}_queue", None)
    request.session.pop(f"quiz_{quiz.id}_progress", None)
    request.session.modified = True
    messages.success(request, "Flags cleared.")
    return redirect("Quizzes:select_questions", quiz_id=quiz.id)
