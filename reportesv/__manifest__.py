# -*- coding: utf-8 -*-
{
    'name': "Reporte-SV",

    'summary': """Allows users to print Purchase Report, Sales Report either taxpayer or consumer""",

    'description': """Creación de Reportes para Compras, Ventas Contribuyentes y Ventas Consumidores
                    Los cuales se encuentran en la direccion: 'Contabilidad/Informes/Informes de auditoría' .
                    Ademas, permite generar el reporte de retaceo a partir de los costos de envio
                    dicho opcion se encuentra en: 'Inventario/Operaciones' """,

    'author': "strategiksv",
    'website': "http://Strategi-k.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Reporting',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_accountant',
                'purchase','stock','strategiksv',
                'stock_landed_costs'],

    # always loaded
    'data': [
        'reports.xml',
        'security/ir.model.access.csv',
        'views/purchase_report_pdf_view.xml',
        'views/taxpayer_report_pdf_view.xml',
        'views/consumer_report_pdf_view.xml',
        'views/landed_cost_report_pdf_view.xml',
        #'views/stock_landed_cost_form.xml',
        'wizard/wizard_purchases_report.xml',
        'wizard/wizard_taxpayer_sales_report.xml',
        'wizard/wizard_consumer_report.xml',
        'wizard/wizard_landed_cost_report.xml',
        #'views/ticket_report_pdf_view.xml',
        #'wizard/wizard_ticket_report.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],
    'instalable': True,
    'auto_install': False,
}
