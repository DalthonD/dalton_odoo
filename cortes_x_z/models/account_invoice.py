import logging
from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from pytz import timezone
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import exceptions
_logger = logging.getLogger(__name__)


class FacturaSV(models.Model):
    _inherit = 'account.invoice'
    monto_letras=fields.Char('Monto en letras',compute='_fill_invoice',store=True)
    excento=fields.Float('excento',compute='_fill_invoice',store=True)
    gravado=fields.Float('gravado',compute='_fill_invoice',store=True)
    nosujeto=fields.Float('nosujeto',compute='_fill_invoice',store=True)
    retenido=fields.Float('retenido',compute='_fill_invoice',store=True)
    percibido=fields.Float('percibido',compute='_fill_invoice',store=True)
    iva=fields.Float('iva',compute='_fill_invoice',store=True)

    @api.one
    @api.depends('amount_total','invoice_line_ids')
    def _fill_invoice(self):
        self.excento=0
        self.gravado=0
        self.nosujeto=0
        self.retenido=0
        self.percibido=0
        self.iva=0
        for line in self.invoice_line_ids:
            if line.invoice_line_tax_ids:
                self.gravado=self.gravado+line.price_subtotal
            else:
                self.excento=self.excento+line.price_subtotal
        for tline in self.tax_line_ids:
            if tline.tax_id.tax_group_id.name=='retencion':
                self.retenido=self.retenido+tline.amount
            if tline.tax_id.tax_group_id.name=='iva':
                self.iva=self.iva+tline.amount
            if tline.tax_id.tax_group_id.name=='percepcion':
                self.percibido=self.percibido+tline.amount
