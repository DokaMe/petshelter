from io import BytesIO, StringIO
import os
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from .models import Animal, Shelter


class BitrixImportTests(TestCase):
    def test_repeated_import_updates_card_and_keeps_id_and_photo(self):
        shelter = Shelter.objects.create(name='Приют')
        env = {
            'BITRIX24_WEBHOOK_URL': 'https://portal.example/rest/25/example-secret/',
            'BITRIX24_ENTITY_TYPE_ID': '1050',
            'BITRIX24_SHELTER_ID': str(shelter.id),
            'BITRIX24_FIELDS': '{"species":"ufCrm2_123","photo":"ufCrm2_127"}',
            'BITRIX24_SPECIES_MAP': '{"101":"cat"}',
            'BITRIX24_ADOPTED_STAGE_IDS': 'DT1050_1:SUCCESS',
        }
        item = {
            'id': 12, 'title': 'Барсик', 'stageId': 'DT1050_1:NEW', 'ufCrm2_123': 101,
            'ufCrm2_127': [{'id': 15, 'urlMachine': 'https://portal.example/rest/getFile?token=example'}],
        }
        sample_image = BytesIO()
        Image.new('RGB', (8, 8)).save(sample_image, format='JPEG')

        def context_response():
            response = MagicMock(status_code=200)
            response.__enter__.return_value = response
            return response

        def post(url, *, json, **kwargs):
            response = context_response()
            if url.endswith('/crm.item.fields.json'):
                response.json.return_value = {
                    'result': {'fields': {'ufCrm2_123': {'type': 'enumeration'}, 'ufCrm2_127': {'type': 'file'}}},
                }
            elif json['start'] == 0:
                response.json.return_value = {'result': {'items': [item]}, 'next': 50}
            else:
                self.assertEqual(json['start'], 50)
                response.json.return_value = {'result': {'items': []}}
            return response

        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media), patch.dict(os.environ, env):
            with patch('animals.management.commands.sync_bitrix_animals.requests.Session') as session:
                http = session.return_value.__enter__.return_value
                http.post.side_effect = post
                photo = context_response()
                photo.iter_content.return_value = [sample_image.getvalue()]
                http.get.return_value = photo

                call_command('sync_bitrix_animals', dry_run=True, stdout=StringIO())
                self.assertFalse(Animal.objects.exists())
                http.get.assert_not_called()

                call_command('sync_bitrix_animals', stdout=StringIO())
                animal = Animal.objects.get()
                self.assertEqual(animal.status, Animal.Status.AVAILABLE)
                self.assertTrue(animal.photo.name.startswith('animals/bitrix/'))
                self.assertTrue(animal.photo.storage.exists(animal.photo.name))
                original_id = animal.id

                item['title'] = 'Барсик-младший'
                item['stageId'] = 'DT1050_1:SUCCESS'
                call_command('sync_bitrix_animals', stdout=StringIO())
                updated = Animal.objects.get()
                self.assertEqual(updated.id, original_id)
                self.assertEqual(updated.photo.name, animal.photo.name)
                self.assertEqual(updated.name, 'Барсик-младший')
                self.assertEqual(updated.status, Animal.Status.ADOPTED)
                self.assertEqual(updated.shelter_id, shelter.id)
                self.assertEqual(updated.species, Animal.Species.CAT)
                http.get.assert_called_once()
