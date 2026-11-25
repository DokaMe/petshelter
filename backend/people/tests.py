from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from animals.models import Animal
from django.contrib.auth import get_user_model
from .models import GuardianRegistration, PersonProfile
from .browser_session import COOKIE_NAME


class BrowserSessionTests(APITestCase):
    def test_cookie_restores_login_and_logout_clears_it(self):
        user = get_user_model().objects.create_user(username='browser-user', password='local-test-password')
        client = APIClient(enforce_csrf_checks=True)
        session = reverse('browser-session')
        credentials = {'username': user.username, 'password': 'local-test-password'}
        origin = {'HTTP_ORIGIN': 'http://localhost:3000'}

        self.assertEqual(client.post(session, credentials, format='json', **origin).status_code, 403)
        initial = client.get(session, **origin)
        self.assertIsNone(initial.data['access'])
        headers = {**origin, 'HTTP_X_CSRFTOKEN': initial.data['csrfToken']}
        sign_in = client.post(session, credentials, format='json', **headers)
        self.assertEqual(sign_in.status_code, 200)
        self.assertNotIn('refresh', sign_in.data)
        self.assertTrue(sign_in.cookies[COOKIE_NAME]['httponly'])
        self.assertIn('no-store', sign_in['Cache-Control'])

        new_page = client.get(session, **origin)
        self.assertTrue(new_page.data['access'])
        self.assertEqual(
            client.get(reverse('current-user'), HTTP_AUTHORIZATION=f"Bearer {new_page.data['access']}").data['username'],
            user.username,
        )
        self.assertEqual(client.delete(session, **origin).status_code, 403)
        self.assertEqual(client.delete(session, **headers).status_code, 204)
        self.assertIsNone(client.get(session, **origin).data['access'])


class RegistrationTests(APITestCase):
    def test_registration_saves_profile_and_user_can_list_guardianships(self):
        data = {
            'username': 'shelter-user',
            'password': 'local-test-password',
            'email': 'shelter-user@example.test',
            'first_name': 'Дарья',
            'last_name': 'Тестова',
            'phone': '+79990000000',
            'city': 'Москва',
            'telegram': '@shelter_test',
        }
        registration = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(registration.status_code, 201)
        self.assertNotIn('password', registration.data)

        login = self.client.post(
            reverse('login'),
            {'username': data['username'], 'password': data['password']},
            format='json',
        )
        self.assertEqual(login.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        profile = self.client.get(reverse('current-user'))
        self.assertEqual(profile.status_code, 200)
        for field in ('first_name', 'last_name', 'phone', 'city', 'telegram'):
            self.assertEqual(profile.data[field], data[field])

        animal = Animal.objects.create(name='Кот', species='cat')
        created = self.client.post(reverse('guardian-create'), {'animal_id': animal.id}, format='json')
        self.assertEqual(created.status_code, 201)
        guardianships = self.client.get(reverse('my-guardianships'))
        self.assertEqual(guardianships.status_code, 200)
        self.assertEqual(guardianships.data[0]['animal']['id'], animal.id)


class GuardianshipCapacityTests(APITestCase):
    def test_fifth_guardian_fills_slot_and_sixth_is_rejected(self):
        animal = Animal.objects.create(name='Барсик', species='cat')
        users = get_user_model().objects
        for i in range(4):
            person = PersonProfile.objects.create(user=users.create_user(username=f'guardian-{i}'))
            GuardianRegistration.objects.create(person=person, animal=animal)
        released = PersonProfile.objects.create(user=users.create_user(username='cancelled-guardian'))
        GuardianRegistration.objects.create(
            person=released, animal=animal, status=GuardianRegistration.Status.CANCELLED,
        )

        detail = reverse('animal-detail', args=[animal.id])
        signup = reverse('guardian-create')
        self.assertEqual(self.client.get(detail).data['guardianship_slots'], 1)

        self.client.force_authenticate(users.create_user(username='guardian-5'))
        self.assertEqual(self.client.post(signup, {'animal_id': animal.id}, format='json').status_code, 201)
        self.assertEqual(self.client.get(detail).data['guardianship_slots'], 0)

        self.client.force_authenticate(users.create_user(username='guardian-6'))
        response = self.client.post(signup, {'animal_id': animal.id}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(animal.guardians.filter(status=GuardianRegistration.Status.ACTIVE).count(), 5)
