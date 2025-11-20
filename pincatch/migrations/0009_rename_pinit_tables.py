from django.db import migrations


def rename_table(schema_editor, old_name, new_name):
    """Rename tables safely, skipping if the source/target state already matches."""
    tables = set(schema_editor.connection.introspection.table_names())
    if new_name in tables:
        # Already renamed manually or from previous migration attempt.
        return
    if old_name not in tables:
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}";')


def rename_pinit_tables(apps, schema_editor):
    rename_table(schema_editor, "pinit_page", "pincatch_page")
    rename_table(schema_editor, "pinit_pagegroup", "pincatch_pagegroup")


def revert_pinit_tables(apps, schema_editor):
    rename_table(schema_editor, "pincatch_page", "pinit_page")
    rename_table(schema_editor, "pincatch_pagegroup", "pinit_pagegroup")


class Migration(migrations.Migration):

    dependencies = [
        ("pincatch", "0008_normalize_page_slugs"),
    ]

    operations = [
        migrations.RunPython(rename_pinit_tables, revert_pinit_tables),
    ]
