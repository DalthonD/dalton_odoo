# -*- coding: utf-8 -*-
##############################################################################


from odoo import api, fields, api, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID



class CryoCustomer(models.Model):
    _inherit = 'res.partner'
    
    mes_cumple=fields.Selection(selection=[('january', 'Enero'),('february', 'Febrero'),('march', 'Marzo'),('april', 'Abril'),('may', 'Mayo'),('june', 'Junio'),('july', 'Julio'),('august', 'Agosto'),('september', 'Septiembre'),('october', 'Octubre'),('november', 'Noviembre'),('december', 'Diciembre')], string='Mes de cumpleaños')
    
    @api.one
    @api.constrains('name', 'mobile','city','email')
    def _compute_nasopupilar(self):
        if (self.customer== True):
            if(self.name==False):
                raise ValidationError("Debe asignar un nombre al cliente")
            if(self.city==False):
                raise ValidationError("Debe ingresar la ciudad del cliente")
            if(self.email==False):
                raise ValidationError("Debe ingresar el email del cliente")
    
