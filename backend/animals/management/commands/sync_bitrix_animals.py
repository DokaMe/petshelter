from hashlib import sha256
from html import unescape

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.html import strip_tags
import requests

from animals.bitrix24 import BitrixClient, BitrixConfig, BitrixError, positive_id
from animals.models import Animal, Shelter


SPECIES = {'cat': 'cat', 'dog': 'dog', 'кот': 'cat', 'кошка': 'cat', 'пёс': 'dog', 'собака': 'dog'}
GENDER = {'male': 'самец', 'female': 'самка', 'самец': 'самец', 'самка': 'самка', 'мальчик': 'самец', 'девочка': 'самка'}


def field_text(item, key):
    value = item.get(key)
    if value is None:
        return ''
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return str(value).strip()
    raise BitrixError(f'Поле {key} должно быть одиночным текстом, числом или ID значения списка.')


def animal_fields(item, config):
    name = field_text(item, 'title')
    if not name or len(name) > 100:
        raise BitrixError('Название карточки должно содержать от 1 до 100 символов.')
    fields = config.fields
    species = field_text(item, fields['species'])
    species = config.species_map.get(species) or SPECIES.get(species.casefold())
    if not species:
        raise BitrixError('Вид питомца не распознан. Проверьте BITRIX24_SPECIES_MAP.')

    gender = field_text(item, fields.get('gender'))
    if gender:
        gender = config.gender_map.get(gender) or GENDER.get(gender.casefold())
        if not gender:
            raise BitrixError('Пол питомца не распознан. Проверьте BITRIX24_GENDER_MAP.')
    return {
        'name': name,
        'shelter_id': config.shelter_id,
        'species': species,
        'gender': gender,
        'age': field_text(item, fields.get('age'))[:100] or None,
        'breed': field_text(item, fields.get('breed'))[:100],
        'description': strip_tags(unescape(field_text(item, fields.get('description')))),
        'status': (
            Animal.Status.ADOPTED if item.get('stageId') in config.adopted_stage_ids else Animal.Status.AVAILABLE
        ),
    }


def photo_fields(item, client, source_key, *, dry_run):
    photo_field = client.config.fields.get('photo')
    if not photo_field:
        return {}
    value = item.get(photo_field)
    if isinstance(value, list):
        value = value[0] if value else None
    if not value:
        return {'bitrix_photo_id': None, 'photo': None}
    if not isinstance(value, dict) or not isinstance(value.get('urlMachine'), str):
        raise BitrixError('Фотография должна приходить из поля «Файл» со ссылкой urlMachine.')
    file_id = positive_id(value.get('id'), 'ID файла')
    if dry_run:
        return {}
    current = Animal.objects.filter(bitrix_source_key=source_key).values('bitrix_photo_id', 'photo').first()
    storage = Animal._meta.get_field('photo').storage
    if current and current['bitrix_photo_id'] == file_id and current['photo'] and storage.exists(current['photo']):
        return {}
    content, extension = client.image(value['urlMachine'])
    folder = sha256(source_key.encode()).hexdigest()[:24]
    file_path = f'animals/bitrix/{folder}/{file_id}.{extension}'
    if not storage.exists(file_path):
        file_path = storage.save(file_path, ContentFile(content))
    return {'bitrix_photo_id': file_id, 'photo': file_path}


class Command(BaseCommand):
    help = 'Загрузить карточки питомцев из CRM Битрикс24 в каталог Django.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Проверить настройки и карточки без записи в БД.')

    def handle(self, *args, dry_run=False, **options):
        count = 0
        created_count = 0
        try:
            config = BitrixConfig.from_env()
            if not Shelter.objects.filter(pk=config.shelter_id).exists():
                raise BitrixError('BITRIX24_SHELTER_ID: в Django нет такого приюта.')
            with requests.Session() as http:
                client = BitrixClient(config, http)
                for item in client.items():
                    item_id = positive_id(item.get('id'), 'ID карточки')
                    source_key = f'{client.portal}:{config.entity_type_id}:{item_id}'
                    try:
                        values = animal_fields(item, config)
                        values.update(photo_fields(item, client, source_key, dry_run=dry_run))
                        if not dry_run:
                            with transaction.atomic():
                                _, created = Animal.objects.update_or_create(bitrix_source_key=source_key, defaults=values)
                            created_count += created
                    except BitrixError as error:
                        raise BitrixError(f'Карточка {item_id}. {error}') from None
                    count += 1
        except BitrixError as error:
            raise CommandError(f'{error} Обработано карточек: {count}.') from None

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Проверено карточек: {count}.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Карточек обработано: {count}. Создано: {created_count}. Обновлено: {count - created_count}.'
            ))
