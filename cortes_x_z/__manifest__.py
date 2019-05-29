# -*- coding: utf-8 -*-
#################################################################################
# Author      :
# Copyright(c):
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#'views/front_inventory_session_pdf_report_template.xml',
#'views/front_inventory_session_thermal_report_template.xml',
#'views/front_inventory_location_pdf_report_template.xml',
#'views/front_inventory_location_thermal_report_template.xml',
#################################################################################
{
    'name': 'POS Reports-SV',
    'category': 'Point of Sale',
    'summary': """Allows user to print X-Report, Z-Report""",
    'description': """Allows user to print X-Report, Z-Report.""",
    'author': "Stretegi-k",
    'website': "http://Strategi-k.com",
    'currency': 'USD',
    'version': '1.0',
    'depends': ['point_of_sale', 'base'],
    'images': ['static/description/main_screenshot.png'],
    'data': [
        'reports.xml',
        'views/pos_report.xml',
        'views/corte_z_pos_sales_report_pdf_template.xml',
        'views/sales_details_pdf_template.xml',
        'views/corte_x_front_sales_report_x_pdf_template.xml',
        'views/pos_config_view.xml',
        'views/front_inventory_session_pdf_report_template.xml',
        'views/front_inventory_session_thermal_report_template.xml',
        'views/front_inventory_location_pdf_report_template.xml',
        'views/front_inventory_location_thermal_report_template.xml',
        'views/pos_static_register.xml',
        'wizard/wizard_pos_sale_report_view.xml',
        'wizard/wizard_sales_details_view.xml',
        'wizard/wizard_pos_x_report.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
