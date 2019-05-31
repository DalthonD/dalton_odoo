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

from odoo import fields, models, api,
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning

class wizard_pos_sale_report(models.TransientModel):
    _name = 'wizard.pos.sale.report'

    @api.model
    def get_ip(self):
        proxy_ip = self.env['res.users'].browse([self._uid]).company_id.report_ip_address or''
        return proxy_ip

    @api.multi
    def print_receipt(self):
        datas = {'ids': self._ids,
                 'form': self.read()[0],
                 'model': 'wizard.pos.sale.report'
                }
        return self.env.ref('cortes_x_z.report_pos_sales_pdf').report_action(self, data=datas)

    session_ids = fields.Many2many('pos.session', 'pos_session_list', 'wizard_id', 'session_id', string="Session(es) Cerradas")
    pos_ids = fields.Many2many('pos.config', 'pos_config_list', 'wizard_id', 'pos_id', string="Punto(s) de venta(s)")
    end_date = fields.Date(string="Fecha de corte", default=date.today())
    report_type = fields.Selection([('thermal', 'Thermal'),
                                    ('pdf', 'PDF')], default='pdf', readonly=True, string="Report Type")
    proxy_ip = fields.Char(string="Proxy IP", default=get_ip)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
