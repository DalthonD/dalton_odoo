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

from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import Warning, RedirectWarning
from datetime import datetime, date, time, timedelta
from pytz import timezone
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

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
    end_date = fields.Date(string="Fecha de Corte", default=date.today())
    report_type = fields.Selection([('thermal', 'Thermal'),
                                    ('pdf', 'PDF')], default='pdf', readonly=True, string="Report Type")
    proxy_ip = fields.Char(string="Proxy IP", default=get_ip)

    @api.onchange('end_date')
    def onchange_date(self):
        if self.end_date and self.end_date > date.today():
            raise Warning(_('La fecha no debe ser superior al día de hoy.'))

    @api.multi
    def get_current_date(self):
        if self._context and self._context.get('tz'):
            tz_name = self._context['tz']
        else:
            tz_name = self.env['res.users'].browse([self._uid]).tz
        if tz_name:
            tz = timezone(tz_name)
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')

    @api.multi
    def get_current_time(self):
        if self._context and self._context.get('tz'):
            tz_name = self._context['tz']
        else:
            tz_name = self.env['res.users'].browse([self._uid]).tz
        if tz_name:
            tz = timezone(tz_name)
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
