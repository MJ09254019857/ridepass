from django.db import migrations

ROUTES = [
    # Bus routes
    ('Cantilan – Carrascal Express', 'Cantilan Terminal', 'Carrascal Terminal', 'bus', 30, 40),
    ('Carrascal – Cantilan Express', 'Carrascal Terminal', 'Cantilan Terminal', 'bus', 30, 40),
    ('Cantilan – Tandag via Madrid', 'Cantilan Terminal', 'Tandag Terminal', 'bus', 50, 90),
    ('Tandag – Cantilan via Madrid', 'Tandag Terminal', 'Cantilan Terminal', 'bus', 50, 90),

    # Van routes
    ('CarCanMadCarLan Van', 'Carrascal Terminal', 'Lanuza Terminal', 'van', 60, 75),
    ('LanCarMadCan Van', 'Lanuza Terminal', 'Cantilan Terminal', 'van', 60, 75),
    ('Cantilan – Carmen Van', 'Cantilan Terminal', 'Carmen Terminal', 'van', 45, 55),
    ('Carmen – Carrascal Van', 'Carmen Terminal', 'Carrascal Terminal', 'van', 35, 45),
    ('Madrid – Tandag Van', 'Madrid Terminal', 'Tandag Terminal', 'van', 40, 50),
    ('Lanuza – Tandag Van', 'Lanuza Terminal', 'Tandag Terminal', 'van', 70, 85),

    # Multicab routes
    ('Cantilan – Madrid Multicab', 'Cantilan Terminal', 'Madrid Terminal', 'multicab', 20, 25),
    ('Madrid – Carmen Multicab', 'Madrid Terminal', 'Carmen Terminal', 'multicab', 15, 20),
    ('Carmen – Lanuza Multicab', 'Carmen Terminal', 'Lanuza Terminal', 'multicab', 18, 22),
    ('Carrascal – Madrid Multicab', 'Carrascal Terminal', 'Madrid Terminal', 'multicab', 22, 28),
    ('Cantilan – Carrascal Multicab', 'Cantilan Terminal', 'Carrascal Terminal', 'multicab', 25, 35),

    # Motorcycle routes
    ('Cantilan Moto – Carrascal', 'Cantilan Terminal', 'Carrascal Terminal', 'motorcycle', 15, 30),
    ('Madrid Moto – Cantilan', 'Madrid Terminal', 'Cantilan Terminal', 'motorcycle', 12, 20),
    ('Carmen Moto – Madrid', 'Carmen Terminal', 'Madrid Terminal', 'motorcycle', 10, 18),
    ('Lanuza Moto – Carmen', 'Lanuza Terminal', 'Carmen Terminal', 'motorcycle', 10, 15),
    ('Carrascal Moto – Madrid', 'Carrascal Terminal', 'Madrid Terminal', 'motorcycle', 12, 22),
]


def seed_routes(apps, schema_editor):
    Route = apps.get_model('core', 'Route')
    if Route.objects.exists():
        return  # Don't overwrite if routes already exist
    for name, origin, destination, transport_type, fare, duration_minutes in ROUTES:
        Route.objects.create(
            name=name,
            origin=origin,
            destination=destination,
            transport_type=transport_type,
            fare=fare,
            duration_minutes=duration_minutes,
            is_active=True,
        )


def unseed_routes(apps, schema_editor):
    Route = apps.get_model('core', 'Route')
    Route.objects.filter(
        name__in=[r[0] for r in ROUTES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_ticket_paymongo_session_id_pending_status'),
    ]

    operations = [
        migrations.RunPython(seed_routes, unseed_routes),
    ]
