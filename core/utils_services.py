from os import name
from fpdf import FPDF
from io import BytesIO
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import re

class FormatHelper():
    ''' '''

    @staticmethod
    def get_field_value(obj, field_name):
        try:
            return obj[field_name]
        except Exception as Error:
            return None

    @staticmethod
    def anonymize(text):
        ret = ''
        for t in re.findall(r"[\w']+|[@]", text):
            t = t.strip()
            if len(t) > 2:
                ret += t[0] + '*' * (len(t) - 2) + t[len(t)-1] + ' '
            else:
                ret += t + ' '
        return ret.strip()

    @classmethod
    def get_data_from_obj(cls, param, obj):
        arr = param.split(".", 1)
        if len(arr) == 1:
            try:
                return obj.__dict__[arr[0]]
            except Exception as Error:
                try:
                    return obj[arr[0]]
                except Exception as Error:
                    try:
                        return eval('obj.' + arr[0])
                    except Exception as Error:
                        return ''
        try:
            return cls.get_data_from_obj(arr[1], eval('obj.' + arr[0]))
        except Exception as Error:
            return ''

    @classmethod
    def replace_data(cls, text, obj):
        for par in re.compile('<param>(.*?)</param>', re.IGNORECASE).findall(text):
            to_replace = cls.get_data_from_obj(par, obj)
            if not to_replace or str(to_replace).endswith('.None'):
                to_replace = ''
            text = text.replace('<param>' + par + '</param>', str(to_replace))
        for par in re.compile('&lt;param&gt;(.*?)&lt;/param&gt;', re.IGNORECASE).findall(text):
            if '>' in par:
                name_par = re.compile('>(\\w.+?)<', re.IGNORECASE).findall(par)[0]
            else:
                name_par = par
            
            to_replace = cls.get_data_from_obj(name_par, obj)
            
            if not to_replace or str(to_replace).endswith('.None'):
                to_replace = ''
            text = text.replace('&lt;param&gt;' + par + '&lt;/param&gt;', str(to_replace))
        return text

    @classmethod
    def replace_data_preparing_html(cls, text, obj):
        for body in re.compile('<body.*>', re.IGNORECASE).findall(text):
            new_body = body + ' <div class="nonEditable">'
            text = text.replace(body, new_body)
            text = text.replace('</body>', '</div></body>')
        for par in re.compile('&lt;param&gt;(.*?)&lt;/param&gt;', re.IGNORECASE).findall(text):
            if '>' in par:
                name_par = re.compile('>(\\w.+?)<', re.IGNORECASE).findall(par)[0]
            else:
                name_par = par
            
            if name_par == 'data' and not cls.get_data_from_obj(name_par, obj):
                to_replace = '<div class="mceEditable">Diligencia ac??</div>'
            else:
                to_replace = cls.get_data_from_obj(name_par, obj)
            
            if not to_replace or str(to_replace).endswith('.None'):
                to_replace = ''
            text = text.replace('&lt;param&gt;' + par + '&lt;/param&gt;', str(to_replace))
        return text

class PDF(FPDF):

    # Page header
    def custom_header(self, pqrs, initial_x_pos, initial_y_pos, sizing_factor, border):
        
        # Basic parameters of pqrs info
        params = [
            ('No. Radicado', pqrs.number),
            ('Fecha', pqrs.date_radicated.strftime('%Y-%m-%d %I:%M:%S %p')),
            ('Anexos', str(len(pqrs.files.all())))
        ]
        self.set_font('Arial', '', 6.0*sizing_factor)
        # Starting position in canvas
        self.set_xy(initial_x_pos, initial_y_pos)
        # Creation of image box
        self.cell(25*sizing_factor, 20.0*sizing_factor, '', border=border)
        # Insertion of image
        self.image('static/correspondence/assets/img/faviconcopy.png', x=initial_x_pos+(2.0*sizing_factor), 
                   y=initial_y_pos+(2.0*sizing_factor), w=20*sizing_factor, h=15*sizing_factor)
        # Creation of basic information table
        self.set_x(initial_x_pos+(25.0*sizing_factor))
        self.cell(50*sizing_factor, 5*sizing_factor, 'NOMBRE DE LA DEPENDENCIA', border=border, align='C')
        self.ln(5*sizing_factor)
        for param in params:
            self.set_x(initial_x_pos+(25.0*sizing_factor))
            self.cell(20.0*sizing_factor, 5.0*sizing_factor, param[0], border=border)
            self.cell(30.0*sizing_factor, 5.0*sizing_factor, param[1], border=border, align='C')
            self.ln(5*sizing_factor)
        
        self.set_x(initial_x_pos)
        # Barcode generation
        self.add_font('Barcode', '', 'static/correspondence/assets/fonts/barcode_font/BarcodeFont.ttf', uni=True)
        self.set_font('Barcode', '', 25*sizing_factor)
        self.cell(75.0*sizing_factor, 15.0*sizing_factor, pqrs.number, border=border, align='C')
        

    # Page footer
    def custom_footer(self):
        # Position from the bottom of the page
        self.set_y(-45)
        self.set_font('Arial', '', 8)
        # Dependency info
        self.multi_cell(0, 5, 'NOMBRE DE LA DEPENDENCIA O GRUPO\n')
        self.set_font('Arial', '', 6)
        self.multi_cell(0, 5, 'DIRECCI??N UBICACI??N DEPENDENCIA O GRUPO\nN??MERO DE CONTACTO')
        self.set_font('Arial', '', 5)
        self.cell(40, 5, 'CORREO ELECTR??NICO O DIRECCI??N SITIO WEB')
        # Page numbering
        self.set_font('Arial', 'I', 8)
        
        self.cell(90, 5, 'P??gina ' + str(self.page_no()) + ' de {nb}', 0, 0, 'C')


