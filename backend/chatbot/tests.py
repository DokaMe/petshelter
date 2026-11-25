from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
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
    @patch('chatbot.assistant.requests.post')
    def test_assistant_receives_catalog_and_returns_only_known_pets(self, post):
        user = get_user_model().objects.create_user(username='reader')
        shelter = Shelter.objects.create(name='Test shelter', city='Test city')
        cat = Animal.objects.create(name='Барсик', species=Animal.Species.CAT, shelter=shelter)
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
