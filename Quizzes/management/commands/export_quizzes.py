from django.core.management.base import BaseCommand
from Quizzes.models import Quiz, Question
import json


class Command(BaseCommand):
    help = "Export all quizzes, questions, and options into a structured dictionary"

    def handle(self, *args, **options):
        data = {}

        for quiz in Quiz.objects.all():
            quiz_data = {
                "title": quiz.title,
                "description": quiz.description,
                "category": quiz.category,
                "questions": []
            }

            questions = Question.objects.filter(quiz=quiz).order_by("order")
            for q in questions:
                question_data = {
                    "text": q.text,
                    "explanation": q.explanation,
                    "options": {
                        "A": q.option_a,
                        "B": q.option_b,
                        "C": q.option_c,
                        "D": q.option_d,
                        "E": q.option_e,
                    },
                    "correct_answer": q.correct_answer
                }

                quiz_data["questions"].append(question_data)

            data[quiz.title] = quiz_data

        # Output JSON and save to file
        output = json.dumps(data, indent=4, ensure_ascii=False)
        print(output)

        with open("quizzes_export.txt", "w", encoding="utf-8") as f:
            f.write(output)

        self.stdout.write(self.style.SUCCESS("✅ Export complete! Data saved to quizzes_export.txt"))
