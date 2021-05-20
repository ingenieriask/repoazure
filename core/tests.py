from django.test import TestCase
from core.services import MailService
from correspondence.services import ECMService

class MailServiceTestCase(TestCase):

    fixtures = ['app_parameter.json', ]
    def test_send_mail(self):

        MailService.send_mail(
            subject='Email subject', 
            body='Email body', 
            from_email=None, 
            to=['jorge.vanegas@skillnet.com.co'])

class ECMServiceTestCase(TestCase):

    fixtures = ['app_parameter.json', ]

    def test_create_record(self):

        ECMService.create_record('test')