from fpdf import FPDF


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
        self.set_y(-51)
        self.set_font('Arial', '', 8)
        # Dependency info
        self.multi_cell(0, 5, 'NOMBRE DE LA DEPENDENCIA O GRUPO\n')
        self.set_font('Arial', '', 6)
        self.multi_cell(0, 5, 'DIRECCIÓN UBICACIÓN DEPENDENCIA O GRUPO\nNÚMERO DE CONTACTO')
        self.set_font('Arial', '', 5)
        self.multi_cell(0, 5, 'CORREO ELECTRÓNICO O DIRECCIÓN SITIO WEB')
        # Page numbering
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Página ' + str(self.page_no()), 0, 0, 'C')
