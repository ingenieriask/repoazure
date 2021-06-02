from django.test import TestCase
from core.services import MailService, RecordCodeService, CalendarService
from correspondence.services import ECMService
'''
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

class RecordCodeServiceTestCase(TestCase):

    fixtures = ['record_consecutive.json', 'app_filing_type.json']

    def test_get_consecutive(self):
        type = 1
        consecutive = RecordCodeService.get_consecutive(type)
        self.assertEqual(consecutive, '12021001suffix')
        consecutive = RecordCodeService.get_consecutive(type)
        self.assertEqual(consecutive, '12021002suffix')
        consecutive = RecordCodeService.get_consecutive(type)
        self.assertEqual(consecutive, '12021003suffix')

    def test_decompile(self):
        code = '{type}-{year}{consecutive:03d}sufix'
        format, digits = RecordCodeService.decompile(code)
        self.assertEqual(format, '{type},-,{year},{consecutive},sufix')
        self.assertEqual(digits, 3)
        
    def test_compile(self):
        format = 'prefix,{type},-,{year},{consecutive},sufix'
        digits = 3
        code = RecordCodeService.compile(format, digits)
        self.assertEqual(code, 'prefix{type}-{year}{consecutive:03d}sufix')
'''
class CalendarServiceTestCase(TestCase):

    fixtures = []

    def test_get_holidays(self):
        year = 2021
        country_code = 'CO'
        self.assertFalse(CalendarService.holidays)
        CalendarService.get_holidays(year, country_code)
        self.assertTrue(f'{country_code}-{year}' in CalendarService.holidays)
