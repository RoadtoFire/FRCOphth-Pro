from django.db import migrations

def fix_categories_order(apps, schema_editor):
    Category = apps.get_model("Quizzes", "Category")

    # 1️⃣  Clean up old or merged names
    renames = {
        "Optics / Oncology": "Optics",
        "FRCOphtn": "FRCOphth Pro",  # just in case
    }
    for old, new in renames.items():
        try:
            old_obj = Category.objects.filter(name=old).first()
            if old_obj:
                new_obj, _ = Category.objects.get_or_create(name=new)
                # move any related questions
                old_obj.questions.update(category=new_obj)
                old_obj.delete()
        except Exception as e:
            print(f"[Migration] rename failed for {old} → {new}: {e}")

    # 2️⃣  Desired order list
    order_list = [
        "Optics",
        "Anatomy",
        "Epidemiology and Biostatistics",
        "Instruments and Investigations",
        "Pathology",
        "Immunology",
        "Microbiology",
        "Embryology",
        "Pharmacology",
        "Biochemistry",
        "Cell Biology",
        "Physiology",
        "Genetics",
    ]

    # 3️⃣  Ensure all exist with proper order
    for index, name in enumerate(order_list, start=1):
        obj, _ = Category.objects.get_or_create(name=name)
        obj.display_order = index
        obj.save()

    print("[Migration] Category names normalized and ordered successfully.")


class Migration(migrations.Migration):

    dependencies = [
        ("Quizzes", "0006_category_remove_question_topic_name_and_more"),  # update if last migration differs
    ]

    operations = [
        migrations.RunPython(fix_categories_order),
    ]
