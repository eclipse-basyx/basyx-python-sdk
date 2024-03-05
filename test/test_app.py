# test_app.py
import unittest
from webapp.app import app  # Adjust the import path based on your actual app location

class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_get_shells(self):
        response = self.client.get('/shells')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])  # Assuming the initial state is an empty list

    def test_post_shells(self):
        mock_data = {'id': 'shell1', 'name': 'Shell 1'}
        response = self.client.post('/shells', json=mock_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, mock_data)  # Check if the returned data matches

# More tests can be added here

if __name__ == '__main__':
    unittest.main()
