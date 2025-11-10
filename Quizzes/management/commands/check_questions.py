# Save this as: Quizzes/management/commands/check_questions.py

from django.core.management.base import BaseCommand
from Quizzes.models import Question, Quiz

class Command(BaseCommand):
    help = 'Check question database structure'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("🔍 CHECKING QUESTION DATABASE")
        self.stdout.write("=" * 60)
        
        # Total questions
        total = Question.objects.count()
        self.stdout.write(f"\n📊 Total Questions: {total}")
        
        # Questions by category
        self.stdout.write("\n📁 Questions by Category:")
        categories = Question.objects.values_list('category__name', flat=True).distinct()
        for cat in categories:
            if cat:
                count = Question.objects.filter(category__name=cat).count()
                self.stdout.write(f"   • {cat}: {count} questions")
            else:
                count = Question.objects.filter(category__isnull=True).count()
                self.stdout.write(f"   • [No Category]: {count} questions")
        
        # Questions by quiz
        self.stdout.write("\n📚 Questions by Quiz:")
        quizzes = Quiz.objects.all()
        for quiz in quizzes:
            count = quiz.questions.count()
            self.stdout.write(f"   • {quiz.title}: {count} questions")
        
        # Sample questions
        self.stdout.write("\n📝 Sample Questions (first 5):")
        for q in Question.objects.all()[:5]:
            category = q.category.name if q.category else "[No Category]"
            quiz = q.quiz.title if q.quiz else "[No Quiz]"
            self.stdout.write(f"   • ID {q.id}: {q.text[:50]}... [{category}] [{quiz}]")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("✅ Check complete!")
        self.stdout.write("=" * 60)