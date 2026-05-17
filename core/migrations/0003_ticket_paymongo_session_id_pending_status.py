from django.db import migrations
# This migration is a no-op placeholder kept for migration chain consistency.
# The paymongo_session_id field was moved to payments.TicketOrder instead.
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_notification_userprofile'),
    ]
    operations = []
