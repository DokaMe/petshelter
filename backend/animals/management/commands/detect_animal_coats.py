from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F

from animals.models import Animal
from chatbot.coat import classify_photo, photo_part
from chatbot.openrouter import AssistantUnavailable


class Command(BaseCommand):
    help = 'Определить окрас животных по фотографиям через OpenRouter.'

    def add_arguments(self, parser):
        parser.add_argument('--animal-id', type=int)
        parser.add_argument('--force', action='store_true', help='Повторить анализ актуальных фото.')

    def handle(self, *args, **options):
        if not settings.OPENROUTER_TOKEN:
            raise CommandError('Задайте OPENROUTER_TOKEN.')
        animals = Animal.objects.filter(coat_color='').exclude(photo__isnull=True).exclude(photo='')
        if options['animal_id'] is not None:
            animals = animals.filter(pk=options['animal_id'])
        if not options['force']:
            animals = animals.exclude(coat_photo_name=F('photo'))

        updated = failed = 0
        for animal in list(animals.order_by('pk')):
            photo_name = animal.photo.name
            photo = photo_part(animal)
            if photo is None:
                failed += 1
                self.stderr.write(f'Карточка {animal.pk}: фото недоступно для анализа.')
                continue
            try:
                color = classify_photo(photo)
            except AssistantUnavailable:
                failed += 1
                self.stderr.write(f'Карточка {animal.pk}: OpenRouter не вернул результат.')
                continue
            updated += Animal.objects.filter(pk=animal.pk, photo=photo_name, coat_color='').update(
                photo_coat=color, coat_photo_name=photo_name,
            )
        self.stdout.write(f'Обновлено карточек: {updated}. Ошибок: {failed}.')
        if failed:
            raise CommandError('Некоторые фотографии не обработаны. Повторите команду после проверки.')
