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
'''
class RecordCodeServiceTestCase(TestCase):

    fixtures = ['record_consecutive.json', 'app_filing_type.json']

    def test_get_consecutive(self):
        consecutive = RecordCodeService.get_consecutive(RecordCodeService.Type.INPUT)
        self.assertEqual(consecutive, '2021000000011')
        consecutive = RecordCodeService.get_consecutive(RecordCodeService.Type.INPUT)
        self.assertEqual(consecutive, '2021000000021')
        consecutive = RecordCodeService.get_consecutive(RecordCodeService.Type.INPUT)
        self.assertEqual(consecutive, '2021000000031')
        consecutive = RecordCodeService.get_consecutive(RecordCodeService.Type.OUTPUT)
        self.assertEqual(consecutive, '2021000000012')
'''
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

class CalendarServiceTestCase(TestCase):

    fixtures = ['app_country.json', ]

    def test_get_holidays(self):
        year = 2021
        country_code = 'CO'
        holidays = CalendarService.get_holidays(year, country_code)
        print(holidays)
        self.assertTrue(holidays)
        holidays = CalendarService.get_holidays(year, country_code)
        print(holidays)
        self.assertTrue(holidays)
'''
