import logging
from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import tools
import pytz
from pytz import timezone
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import exceptions
_logger = logging.getLogger(__name__)

class stock_landed_cost(models.Model):
    _name = "stock.landed.cost"
    _inherit = "stock.landed.cost"

    def get_invoices_inf(self):
        data={}
        purchases = set()
        invoices = set()
        if self:
            for p in self.picking_ids:
                purchase_order_obj = self.env['purchase.order'].search([('id','=',p.purchase_id)])
                raise ValidationError("Contenido devuelto: %s" % purchase_order_obj)
        else:
            return data
