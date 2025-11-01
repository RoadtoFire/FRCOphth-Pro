# dump_utf8.py
import os
import django
import json
from django.apps import apps
from django.core import serializers

# --- Step 1: Setup Django environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MedicalQuiz.settings')
django.setup()

# --- Step 2: Exclude system/internal models ---
EXCLUDES = {
    'auth.permission',
    'contenttypes',
    'sessions',
    'admin.logentry'
}

# --- Step 3: Serialize all non-excluded models ---
def get_all_objects():
    for model in apps.get_models():
        label = f"{model._meta.app_label}.{model._meta.model_name}"
        if label not in EXCLUDES:
            for obj in model.objects.all():
                yield obj

data = serializers.serialize('json', get_all_objects(), indent=2)

# --- Step 4: Write to UTF-8 file safely ---
with open('data.json', 'w', encoding='utf-8') as f:
    f.write(data)

print("✅ Data exported successfully to data.json (UTF-8 encoded)")
