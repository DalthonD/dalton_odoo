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

class stock_valuation_adjusment_lines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    additional_landed_cost = fields.Float(string="Costes adicionales en destino", required=True)
