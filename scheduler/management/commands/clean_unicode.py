from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import CustomUser
import re

class Command(BaseCommand):
    help = 'Clean Unicode characters from user data'

    def handle(self, *args, **options):
        self.stdout.write('Starting Unicode cleanup...')
        
        # Clean user data
        users_updated = 0
        for user in CustomUser.objects.all():
            updated = False
            
            # Clean text fields
            text_fields = ['name', 'username', 'email', 'phone', 'business_name', 
                          'business_address', 'goals', 'session_focus', 'session_note']
            
            for field in text_fields:
                value = getattr(user, field, None)
                if value and isinstance(value, str):
                    # Remove or replace problematic Unicode characters
                    cleaned_value = re.sub(r'[^\x00-\x7F]+', '?', value)
                    if cleaned_value != value:
                        setattr(user, field, cleaned_value)
                        updated = True
            
            if updated:
                user.save()
                users_updated += 1
                self.stdout.write(f'Updated user: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned {users_updated} users')
        )
