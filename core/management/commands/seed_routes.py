from django.core.management.base import BaseCommand
from core.models import Route
class Command(BaseCommand):
    help = 'Seed sample routes'
    def handle(self, *args, **kwargs):
        Route.objects.all().delete()
        routes = [
            ('CarCanMadCarLan Express','Caraga Terminal','City Center','bus',25,35),
            ('Maharlika Route 1','Maharlika Terminal','SM City','van',30,45),
            ('Downtown Multicab A','Public Market','City Hall','multicab',12,15),
            ('Suburb Van Line 2','Rosario','Provincial Hospital','van',40,60),
            ('Night Bus Route 5','Bus Terminal','Surigao Port','bus',50,80),
            ('Tandag Multicab','Tandag Terminal','Tandag Market','multicab',10,10),
            ('Airport Shuttle','City Center','Bancasi Airport','van',80,50),
            ('Moto Express 1','Barangay Hall','Elementary School','motorcycle',8,8),
        ]
        for name,origin,dest,ttype,fare,dur in routes:
            Route.objects.create(name=name,origin=origin,destination=dest,transport_type=ttype,fare=fare,duration_minutes=dur)
        self.stdout.write(self.style.SUCCESS(f'Created {len(routes)} routes.'))
