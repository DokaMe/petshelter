from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import override_settings
from PIL import Image
from django.urls import reverse
from rest_framework.test import APITestCase

from animals.models import Animal, Shelter
from .models import ChatConversation


@override_settings(OPENROUTER_TOKEN='')
class ConversationMessagesTests(APITestCase):
    def test_owner_can_send_and_read_messages_but_other_user_cannot(self):
        users = get_user_model().objects
        owner = users.create_user(username='owner')
        another_user = users.create_user(username='another')
        shelter = Shelter.objects.create(name='Test shelter', city='Test city')
        self.client.force_authenticate(owner)

        conversation = self.client.post(
            reverse('conversation-create'),
            {
                'shelter': shelter.id,
                'purpose': 'undecided',
                'species': 'any',
                'housing': 'apartment',
                'communication_style': 'consultant',
                'questionnaire': {
                    'gender': 'any',
                    'has_children': False,
                    'has_other_animals': False,
                    'had_animals_before': None,
                    'activity': 'calm',
                },
            },
            format='json',
        )
        self.assertEqual(conversation.status_code, 201)
        self.assertEqual(conversation.data['questionnaire']['activity'], 'calm')
        messages_url = reverse('message-create', args=[conversation.data['session_id']])

        sent = self.client.post(messages_url, {'content': 'Есть ли кошки?'}, format='json')
        self.assertEqual(sent.status_code, 201)
        self.assertIn('Расскажите немного больше', sent.data['bot_message']['content'])
        history = self.client.get(messages_url)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.data, [sent.data['user_message'], sent.data['bot_message']])

        self.client.force_authenticate(another_user)
        self.assertEqual(self.client.get(messages_url).status_code, 404)
        self.assertEqual(
            self.client.post(messages_url, {'content': 'Есть ли кошки?'}, format='json').status_code,
            404,
        )

    def test_friend_conversation_replies_informally(self):
        user = get_user_model().objects.create_user(username='friend')
        shelter = Shelter.objects.create(name='Test shelter', city='Test city')
        conversation = ChatConversation.objects.create(
            user=user,
            shelter=shelter,
            purpose=ChatConversation.Purpose.ADOPTION,
            species=ChatConversation.Species.CAT,
            housing=ChatConversation.Housing.APARTMENT,
            communication_style=ChatConversation.CommunicationStyle.FRIEND,
        )
        self.client.force_authenticate(user)
        messages_url = reverse('message-create', args=[conversation.session_id])

        sent = self.client.post(messages_url, {'content': 'Есть ли кошки?'}, format='json')

        self.assertEqual(sent.status_code, 201)
        self.assertIn('какого питомца ты ищешь', sent.data['bot_message']['content'])

    @override_settings(OPENROUTER_TOKEN='test-key')
    @patch('chatbot.openrouter.requests.post')
    def test_assistant_receives_catalog_and_returns_only_known_pets(self, post):
        user = get_user_model().objects.create_user(username='reader')
        shelter = Shelter.objects.create(name='Test shelter', city='Test city')
        cat = Animal.objects.create(
            name='Барсик', species=Animal.Species.CAT, shelter=shelter, coat_color='серый полосатый',
        )
        dog = Animal.objects.create(name='Амир', species=Animal.Species.DOG, shelter=shelter)
        conversation = ChatConversation.objects.create(
            user=user, shelter=shelter, purpose=ChatConversation.Purpose.ADOPTION,
            species=ChatConversation.Species.CAT, housing=ChatConversation.Housing.APARTMENT,
            communication_style=ChatConversation.CommunicationStyle.FRIEND,
        )
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'choices': [{'message': {'content':
            f'{{"answer":"Посмотри на Барсика.","animal_ids":[{cat.id},{dog.id},{cat.id}]}}'
        }}]}
        self.client.force_authenticate(user)

        result = self.client.post(
            reverse('message-create', args=[conversation.session_id]),
            {'content': 'Предложи кота'}, format='json',
        )

        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data['bot_message']['content'], 'Посмотри на Барсика.')
        self.assertEqual([item['id'] for item in result.data['animals']], [cat.id])
        instructions, context, _ = post.call_args.kwargs['json']['messages']
        self.assertIn('на ты', instructions['content'])
        self.assertIn('Барсик', context['content'])
        self.assertNotIn('Амир', context['content'])
        self.assertIn('серый полосатый', context['content'])
        self.assertEqual(result.data['animals'][0]['coat_color_source'], 'shelter')

    @override_settings(OPENROUTER_TOKEN='test-key')
    @patch('chatbot.openrouter.requests.post')
    def test_selected_pet_and_current_photo_are_sent_to_openrouter(self, post):
        user = get_user_model().objects.create_user(username='photo-reader')
        shelter = Shelter.objects.create(name='Test shelter')
        cat = Animal.objects.create(name='Барсик', species='cat', shelter=shelter)
        conversation = ChatConversation.objects.create(
            user=user, shelter=shelter, purpose='adoption', species='any', housing='apartment',
            communication_style='consultant', selected_animal=cat,
        )
        self.client.force_authenticate(user)
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            'choices': [{'message': {'content': '{"answer":"По фото кот рыжий.","animal_ids":[]}'}}],
        }
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            image = BytesIO()
            Image.new('RGB', (32, 32), 'orange').save(image, format='PNG')
            cat.photo.save('barsik.png', ContentFile(image.getvalue()))
            result = self.client.post(
                reverse('message-create', args=[conversation.session_id]),
                {'content': 'Какого он цвета?'}, format='json',
            )
            self.assertEqual(result.status_code, 201)
            messages = post.call_args.kwargs['json']['messages']
            parts = messages[1]['content']
            self.assertIn(f'"selected_animal_id": {cat.pk}', parts[0]['text'])
            self.assertIn(f'ID {cat.pk}', parts[1]['text'])
            self.assertTrue(parts[2]['image_url']['url'].startswith('data:image/jpeg;base64,'))
            self.assertEqual(messages[-1]['content'], 'Какого он цвета?')

            post.return_value.json.return_value = {
                'choices': [{'message': {'content': '{"coat_color":"рыжий"}'}}],
            }
            call_command('detect_animal_coats', stdout=StringIO())
            cat.refresh_from_db()
            self.assertEqual(cat.coat_info, ('рыжий', 'photo'))
            post.reset_mock()
            call_command('detect_animal_coats', stdout=StringIO())
            post.assert_not_called()
            cat.photo.save('new-barsik.png', ContentFile(image.getvalue()))
            self.assertEqual(cat.coat_info, ('', None))
