from django.db import migrations


def remove_duplicates(apps, schema_editor):
    """
    Before adding the unique constraint, remove any duplicate (id_object, date, field)
    rows from FinancialData, keeping the one with the lowest primary key.
    """
    FinancialData = apps.get_model('quotes', 'FinancialData')
    seen = {}
    to_delete = []

    for row in FinancialData.objects.order_by('id').values_list('id', 'id_object_id', 'date', 'field'):
        pk, id_object_id, date, field = row
        key = (id_object_id, date, field)
        if key in seen:
            to_delete.append(pk)
        else:
            seen[key] = pk

    if to_delete:
        deleted_count, _ = FinancialData.objects.filter(id__in=to_delete).delete()
        print(f"Removed {deleted_count} duplicate FinancialData rows.")


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0011_alter_financialdata_options_alter_order_portfolio'),
    ]

    operations = [
        migrations.RunPython(remove_duplicates, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='financialdata',
            unique_together={('id_object', 'date', 'field')},
        ),
    ]
