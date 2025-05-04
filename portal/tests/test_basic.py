from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class BasicTestCase(TestCase):
    """Basic test case to verify test setup."""
    
    def test_basic(self):
        """Basic test to verify test setup."""
        self.assertEqual(1 + 1, 2)
