import json
import logging

from django.conf import settings
import requests


logger = logging.getLogger(__name__)


class AssistantUnavailable(Exception):
    pass


def complete_json(messages, *, max_tokens, temperature):
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {settings.OPENROUTER_TOKEN}'},
            json={
                'model': settings.OPENROUTER_MODEL,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'response_format': {'type': 'json_object'},
            },
            timeout=(4, 17),
        )
        if response.status_code != 200:
            logger.warning('OpenRouter returned HTTP %s', response.status_code)
            raise AssistantUnavailable
        result = json.loads(response.json()['choices'][0]['message']['content'])
        if not isinstance(result, dict):
            raise ValueError
        return result
    except (requests.RequestException, AttributeError, TypeError, KeyError, IndexError, ValueError):
        logger.warning('OpenRouter completion failed or returned an unexpected format')
        raise AssistantUnavailable from None
