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
        if self:
            invoices = """select f.date_invoice as fecha, f.reference as referencia
            --,f.amount_total,s.name,s.sv_declaracion,s.date,p.name,po.name,p.origin,f.origin
            from stock_landed_cost s
            inner join stock_landed_cost_stock_picking_rel sp on s.id=sp.stock_landed_cost_id inner join stock_picking p on p.id=sp.stock_picking_id
            inner join purchase_order_stock_picking_rel pp on p.id=pp.stock_picking_id inner join purchase_order po on  po.id=pp.purchase_order_id
            inner join account_invoice_purchase_order_rel ip on po.id=ip.purchase_order_id inner join account_invoice f on f.id=ip.account_invoice_id
            where s.sv_declaracion={0} order by f.date_invoice desc;""".format(self.sv_declaracion)
            self._cr.execute(invoices)
            if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
                data = self._cr.dictfetchall()
            return data
        else:
            return data
