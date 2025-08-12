from django.test import TestCase
from .models import User

class UserModelTest(TestCase):
    def test_user_creation(self):
        user = User.objects.create(username='testuser', password='pass123')
        self.assertEqual(user.username, 'testuser')
