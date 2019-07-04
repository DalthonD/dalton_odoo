from odoo import fields, models, api, _
from odoo.exceptions import Warning, RedirectWarning
from datetime import datetime, date, time, timedelta
from pytz import timezone
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

class wizard_sv_consumer_report(models.TransientModel):
    _name = 'wizard.sv.consumer.report'

    company_id=fields.Many2one('res.company', string="Company", help='Company',default=lambda self: self.env.user.company_id.id)
    date_month = fields.Selection([('1','Enero'),('2','Febrero'),('3','Marzo'),('4','Abril'),('5','Mayo'),('6','Junio'),('7','Julio'),('8','Agosto'),('9','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')],string='Mes de facturación', default='5',required=True)
    date_year = fields.Integer("Año de facturación", default=2019, requiered=True)
    stock_location_id=fields.Many2one('stock.location', string="Sucursal", help="Sucursal de la que se desea el Libro de IVA",default=lambda self: self.env.user.sucursal_id.id)

    @api.multi
    def print_consumer_sales_report(self):
        datas = {'ids': self._ids,
                 'form': self.read()[0],
                 'model': 'wizard.sv.consumer.report'}
        return self.env.ref('reportesv_sucursal.report_consumer_sales_pdf').report_action(self, data=datas)
