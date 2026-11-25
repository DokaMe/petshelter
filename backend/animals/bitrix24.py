from dataclasses import dataclass, field
from io import BytesIO
import json
import os
import re
from urllib.parse import urlsplit

from PIL import Image, UnidentifiedImageError
import requests


class BitrixError(Exception):
    pass


def positive_id(value, label):
    text = str(value)
    if len(text) > 19 or not text.isascii() or not text.isdecimal() or not 0 < int(text) <= 2**63 - 1:
        raise BitrixError(f'{label}: ожидается положительное целое число.')
    return int(text)


def json_mapping(name):
    try:
        value = json.loads(os.getenv(name) or '{}')
    except ValueError:
        raise BitrixError(f'{name}: укажите JSON-объект.') from None
    if not isinstance(value, dict) or any(not isinstance(item, str) for item in value.values()):
        raise BitrixError(f'{name}: укажите JSON-объект со строковыми значениями.')
    return value


@dataclass(frozen=True)
class BitrixConfig:
    webhook_url: str = field(repr=False)
    entity_type_id: int
    shelter_id: int
    fields: dict[str, str]
    species_map: dict[str, str]
    gender_map: dict[str, str]
    adopted_stage_ids: frozenset[str]

    @classmethod
    def from_env(cls):
        url = os.getenv('BITRIX24_WEBHOOK_URL', '').strip().rstrip('/')
        try:
            parsed = urlsplit(url)
        except ValueError:
            raise BitrixError('BITRIX24_WEBHOOK_URL: некорректный адрес вебхука.') from None
        if (
            parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment
            or not re.fullmatch(r'/rest/[0-9]+/[A-Za-z0-9_-]+', parsed.path)
        ):
            raise BitrixError('BITRIX24_WEBHOOK_URL: вставьте HTTPS-адрес вебхука до имени метода.')
        fields = json_mapping('BITRIX24_FIELDS')
        allowed_fields = {'species', 'gender', 'age', 'breed', 'description', 'photo'}
        if not fields.get('species') or fields.keys() - allowed_fields or any(
            not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', value) for value in fields.values()
        ):
            raise BitrixError('BITRIX24_FIELDS: укажите код поля species и нужные дополнительные поля.')
        species_map = json_mapping('BITRIX24_SPECIES_MAP')
        if set(species_map.values()) - {'cat', 'dog'}:
            raise BitrixError('BITRIX24_SPECIES_MAP: допустимые значения cat и dog.')
        gender_map = json_mapping('BITRIX24_GENDER_MAP')
        if set(gender_map.values()) - {'самец', 'самка'}:
            raise BitrixError('BITRIX24_GENDER_MAP: допустимые значения самец и самка.')
        return cls(
            url,
            positive_id(os.getenv('BITRIX24_ENTITY_TYPE_ID'), 'BITRIX24_ENTITY_TYPE_ID'),
            positive_id(os.getenv('BITRIX24_SHELTER_ID'), 'BITRIX24_SHELTER_ID'),
            fields,
            species_map,
            gender_map,
            frozenset(
                stage.strip() for stage in os.getenv('BITRIX24_ADOPTED_STAGE_IDS', '').split(',')
                if stage.strip()
            ),
        )


class BitrixClient:
    def __init__(self, config: BitrixConfig, http: requests.Session):
        self.config = config
        self.http = http
        self.portal = urlsplit(config.webhook_url).netloc.lower()

    def _call(self, method, **params):
        try:
            with self.http.post(
                f'{self.config.webhook_url}/{method}.json',
                json=params, timeout=(5, 20), allow_redirects=False,
            ) as response:
                status = response.status_code
                data = response.json()
        except (requests.RequestException, ValueError):
            raise BitrixError(f'{method}: не удалось получить ответ Битрикс24.') from None
        if not isinstance(data, dict):
            raise BitrixError(f'{method}: неожиданный формат ответа.')
        if status != 200 or 'error' in data:
            error = data.get('error', '')
            safe_code = error if isinstance(error, str) and re.fullmatch(r'[A-Za-z0-9_]{1,64}', error) else ''
            raise BitrixError(f'{method}: ошибка Битрикс24 HTTP {status} {safe_code}'.strip())
        if not isinstance(data.get('result'), dict):
            raise BitrixError(f'{method}: в ответе нет result.')
        return data

    def items(self):
        entity = self.config.entity_type_id
        fields = self._call('crm.item.fields', entityTypeId=entity)['result'].get('fields')
        if not isinstance(fields, dict):
            raise BitrixError('crm.item.fields: Битрикс24 не вернул описание полей.')
        missing = set(self.config.fields.values()) - fields.keys()
        if missing:
            raise BitrixError(f'Поля не найдены. Проверьте BITRIX24_FIELDS: {", ".join(sorted(missing))}.')
        photo_field = self.config.fields.get('photo')
        if photo_field and (not isinstance(fields[photo_field], dict) or fields[photo_field].get('type') != 'file'):
            raise BitrixError('Поле photo должно быть полем CRM типа «Файл».')
        select = list(dict.fromkeys(['id', 'title', 'stageId', *self.config.fields.values()]))
        start = 0
        while True:
            data = self._call('crm.item.list', entityTypeId=entity, select=select, order={'id': 'ASC'}, start=start)
            items = data['result'].get('items')
            if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
                raise BitrixError('crm.item.list: Битрикс24 не вернул список элементов.')
            yield from items
            if 'next' not in data or data['next'] is None:
                break
            next_page = positive_id(data['next'], 'Номер следующей страницы')
            if next_page <= start:
                raise BitrixError('crm.item.list: неверный номер следующей страницы.')
            start = next_page

    def image(self, url):
        try:
            parsed = urlsplit(url)
        except ValueError:
            raise BitrixError('Некорректная ссылка на фото.') from None
        if parsed.scheme != 'https' or parsed.netloc.lower() != self.portal or parsed.username or parsed.password:
            raise BitrixError('Ссылка на фото должна вести на тот же HTTPS-портал Битрикс24.')
        max_bytes = 10 * 1024 * 1024
        data = bytearray()
        try:
            with self.http.get(url, stream=True, timeout=(5, 20), allow_redirects=False) as response:
                if response.status_code != 200:
                    raise BitrixError(f'Битрикс24 не отдал фото. HTTP {response.status_code}.')
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    data.extend(chunk)
                    if len(data) > max_bytes:
                        raise BitrixError('Фото в Битрикс24 больше 10 МБ.')
        except requests.RequestException:
            raise BitrixError('Не удалось скачать фото с Битрикс24.') from None
        extensions = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}
        try:
            with Image.open(BytesIO(data)) as image:
                extension = extensions.get(image.format)
                if not extension or image.width * image.height > 24_000_000:
                    raise BitrixError('Фото должно быть JPEG, PNG или WebP до 24 мегапикселей.')
                image.verify()
        except (UnidentifiedImageError, Image.DecompressionBombError, ValueError, OSError):
            raise BitrixError('Файл из Битрикс24 не удалось прочитать как изображение.') from None
        return bytes(data), extension
