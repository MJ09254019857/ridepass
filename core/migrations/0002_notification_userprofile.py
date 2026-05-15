from django.db import migrations

class Migration(migrations.Migration):
    """
    No-op: Notification and UserProfile are already created in 0001_initial.
    This migration is kept only to preserve the migration chain.
    """
    dependencies = [
        ('core', '0001_initial'),
    ]
    operations = []
