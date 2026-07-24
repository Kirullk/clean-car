from django.core.management.base import BaseCommand
from vkbot.vkbot import main


class Command(BaseCommand):
    help = 'Запускает VK бота'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Запуск VK бота...')
        main()
