import unittest
from app import app

class BasicRoutesTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_services(self):
        response = self.client.get('/services')
        self.assertEqual(response.status_code, 200)

    def test_gallery(self):
        response = self.client.get('/gallery')
        self.assertEqual(response.status_code, 200)

    def test_booking(self):
        response = self.client.get('/booking')
        self.assertEqual(response.status_code, 200)

    def test_contact(self):
        response = self.client.get('/contact')
        self.assertEqual(response.status_code, 200)

    def test_admin(self):
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user'] = 'dummy'
            response = c.get('/logout', follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/', response.headers['Location'])

if __name__ == '__main__':
    unittest.main()
