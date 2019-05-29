# -*- coding: utf-8 -*-
#################################################################################
# Author      :
# Copyright(c):
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import models, api, _

class sales_details_pdf_template(models.AbstractModel):
    _name = 'report.cortes_x_z.sales_details_pdf_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('cortes_x_z.sales_details_pdf_template')
        if data and data.get('form') and data.get('form').get('user_ids'):
            docids = self.env['wizard.sales.details'].browse(data['form']['user_ids'])
        return {'doc_ids': self.env['wizard.sales.details'].browse(data.get('ids')),
                'doc_model': report.model,
                'docs': self.env['wizard.sales.details'].browse(data['form']['user_ids']),
                'data': data,
                }

class front_sales_report_x_pdf_template(models.AbstractModel):
    _name = 'report.cortes_x_z.front_sales_report_x_pdf_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('cortes_x_z.front_sales_report_x_pdf_template')
        if data and data.get('form') and data.get('form').get('session_ids'):
            docids = self.env['pos.session'].browse(data['form']['session_ids'])
        return {'doc_ids': self.env['wizard.pos.x.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['pos.session'].browse(data['form']['session_ids']),
                'data': data,
                }

class pos_sales_report_pdf_template(models.AbstractModel):
    _name = 'report.cortes_x_z.pos_sales_report_pdf_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('cortes_x_z.pos_sales_report_pdf_template')
        if data and data.get('form') and data.get('form').get('session_ids'):
            docids = self.env['pos.session'].browse(data['form']['session_ids'])
        return {'doc_ids': self.env['wizard.pos.sale.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['pos.session'].browse(data['form']['session_ids']),
                'data': data,
                }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
