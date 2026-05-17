from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_topuporder_mobile_number_and_more'),
        ('core', '0003_ticket_paymongo_session_id_pending_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('route_id', models.IntegerField()),
                ('route_name', models.CharField(max_length=200)),
                ('amount', models.PositiveIntegerField(help_text='Amount in centavos')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed')],
                    default='pending',
                    max_length=20,
                )),
                ('paymongo_link_id', models.CharField(blank=True, max_length=100)),
                ('checkout_url', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ticket_orders',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('ticket', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='order',
                    to='core.ticket',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
