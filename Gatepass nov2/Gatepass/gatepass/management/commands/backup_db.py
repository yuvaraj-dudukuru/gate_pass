from django.core.management.base import BaseCommand
from django.conf import settings
import os
import datetime
import subprocess

class Command(BaseCommand):
    help = 'Backup PostgreSQL database'

    def handle(self, *args, **kwargs):
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        
        db_settings = settings.DATABASES['default']
        env = dict(os.environ)
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        cmd = [
            'pg_dump',
            '-h', db_settings['HOST'],
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-f', backup_file
        ]
        
        try:
            subprocess.run(cmd, env=env, check=True)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully backed up database to {backup_file}')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to backup database: {str(e)}')
            )