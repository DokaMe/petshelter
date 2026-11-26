from base64 import b64encode
from io import BytesIO
import logging
import re

from PIL import Image, ImageOps

from .openrouter import AssistantUnavailable, complete_json


logger = logging.getLogger(__name__)

COAT_INSTRUCTIONS = (
    'Под окрасом понимай видимые цвета шерсти и заметный рисунок, например полосы или пятна. '
    'Учитывай только шерсть самого питомца. Цвет глаз, ошейника и фона не включай. '
    'При плохом свете, нескольких животных или если признак не виден, укажи неопределённость. '
    'Не выводи породу, пол или состояние здоровья из окраса.'
)

COAT_QUERY = re.compile(
    r'\b(?:окрас\w*|цвет\w*|шерст\w*|маст\w*|расцвет\w*|полосат\w*|пятнист\w*|'
    r'однотон\w*|тр[её]хцвет\w*|двухцвет\w*|черепахов\w*|табби|рыж\w*|'
    r'ч[её]рн\w*|бел(?:ый|ая|ое|ые|ого|ую|ых|ыми|ым|ом)|'
    r'сер(?:ый|ая|ое|ые|ого|ую|ых|ыми|ым|ом|о)|коричнев\w*|золотист\w*|бежев\w*|кремов\w*)\b',
    re.IGNORECASE,
)


def is_coat_question(text):
    return bool(COAT_QUERY.search(text))


def photo_part(animal):
    if not animal.photo:
        return None
    try:
        with animal.photo.open('rb') as file, Image.open(file) as original:
            if original.width * original.height > 24_000_000:
                return None
            image = ImageOps.exif_transpose(original)
            image.thumbnail((512, 512))
            buffer = BytesIO()
            image.convert('RGB').save(buffer, format='JPEG', quality=82)
    except (Image.DecompressionBombError, OSError, ValueError, SyntaxError):
        logger.warning('Cannot read image for animal %s', animal.pk)
        return None

    encoded = b64encode(buffer.getvalue()).decode('ascii')
    return {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{encoded}', 'detail': 'low'}}


def classify_photo(photo):
    data = complete_json([
        {
            'role': 'system',
            'content': (
                f'Опиши окрас питомца на фото по-русски. {COAT_INSTRUCTIONS} '
                'Верни JSON с полем coat_color. Значение — краткое описание до 160 символов '
                'или null, если по фото нельзя определить окрас.'
            ),
        },
        {'role': 'user', 'content': [{'type': 'text', 'text': 'Определи окрас по фото.'}, photo]},
    ], max_tokens=100, temperature=0)
    color = data.get('coat_color')
    if 'coat_color' not in data or (color is not None and not isinstance(color, str)):
        raise AssistantUnavailable
    return ' '.join(color.split())[:160] if color else ''
