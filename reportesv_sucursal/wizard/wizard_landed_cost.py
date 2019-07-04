from odoo import fields, models, api, _
from odoo.exceptions import Warning, RedirectWarning
from datetime import datetime, date, time, timedelta
from pytz import timezone
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

class wizard_sv_stock_landed_cost_report(models.TransientModel):
    _name = 'wizard.sv.stock.landed.cost.report'

    company_id=fields.Many2one('res.company', string="Company", help='Company',default=lambda self: self.env.user.company_id.id)
    stock_landed_cost_ids=fields.Many2many('stock.landed.cost', 'stock_landed_cost_list', 'wizard_id','cost_id', string="Costos de envío", help='Costos incurridos en la adquisición de mercancía')

    @api.multi
    def print_landed_cost_report(self):
        datas = {'ids': self._ids,
                 'form': self.read()[0],
                 'model': 'wizard.sv.stock.landed.cost.report'}
        return self.env.ref('reportesv_sucursal.report_stock_landed_cost_pdf').report_action(self, data=datas)
