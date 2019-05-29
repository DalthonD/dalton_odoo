# -*- coding: utf-8 -*-
##############################################################################

from odoo import api, fields, api, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID


class cryo_sv_pos(models.Model):
    _inherit = 'pos.config'
    header_ticket=fields.Char("Header Ticket")
    footer_ticket=fields.Char("Footer Ticket")
    header_recibo=fields.Char("Header Recibo")
    footer_recibo=fields.Char("Footer Recibo")
    ticket_sequence=fields.Many2one('ir.sequence',string='Numeracion de tickets',help='Numeracion de tickets')
    recibo_sequence=fields.Many2one('ir.sequence',string='Numeracion de recibos',help='Numeracion de recibos')
    ticket_number=fields.Integer("Proximo ticket")
    recibo_number=fields.Integer("Proximo recibo")


class cryo_sv_pos_session(models.Model):
    _inherit = 'pos.session'
    ticket_number=fields.Integer("Proximo ticket")
    recibo_number=fields.Integer("Proximo recibo")

    @api.model
    def create(self, values):
        res = super(cryo_sv_pos_session, self).create(values)
        lastnumber=False
        session=self.env['pos.session'].search(['&',('config_id','=',res.config_id.id),('id','!=',res.id)],limit=1,order='id desc')
        if (session):
            res.write({'sequence_number':session.sequence_number+1})
        else:
            res.write({'sequence_number':1})
        return res


class cryo_sv_pos_order(models.Model):
    _inherit = 'pos.order'
    ticket_number=fields.Integer("Numero ticket")
    recibo_number=fields.Integer("Numero recibo")

    @api.model
    def create_from_ui(self, orders):
        order_ids = super(cryo_sv_pos_order,self).create_from_ui(orders)
        for index,order in enumerate(orders):
            order_data = order.get('data')
            pos_order = self.env['pos.order'].search([('pos_reference','=', order_data.get('name'))])
            if order_data and order_data.get('ticket_number') and pos_order:
                pos_order.write({'ticket_number':order_data.get('ticket_number')})
                config=self.env['pos.config'].search([('id','=',pos_order.config_id.id)],limit=1,order='id desc')
                config.write({'ticket_number':order_data.get('ticket_number')})
            if order_data and order_data.get('recibo_number') and pos_order:
                pos_order.write({'recibo_number':order_data.get('recibo_number')})
                config=self.env['pos.config'].search([('id','=',pos_order.config_id.id)],limit=1,order='id desc')
                config.write({'recibo_number':order_data.get('recibo_number')})
        return order_ids

class cryo_sv_wallet_pricelist(models.Model):
    _name='cryo.wallet.amount'
    name= fields.Char("Rangos de recarga")
    comment=fields.Text("Description")
    amount=fields.Float("Monto de la recarga")
    start_date=fields.Date("Fecha de inicio")
    end_date=fields.Date("Fecha de inicio")
    pricelist=fields.Many2one('product.pricelist',string='Listas de precios',help='Numeracion de recibos')

class cryo_sv_wallet_amount(models.Model):
    _inherit = 'pos.wallet.transaction'
    prueba= fields.Char("Prueba de recarga")

    @api.model
    def create(self, values):
        res = super(cryo_sv_wallet_amount, self).create(values)
        if (values['payment_type']=='CREDIT'):
            prices=False
            lst=self.env['cryo.wallet.amount'].search([('id','>',0)])
            lst.sorted(key=lambda r: r.amount)
            for am in lst:
                saldo=values['amount']
                if (saldo>=am.amount):
                    prices=am.pricelist
            if (prices!=False):
                cliente=self.env['res.partner'].search([("id",'=',values['partner_id'])],limit=1)
                cliente.property_product_pricelist=prices.id
        else:
            wallet = self.env['pos.wallet'].search([("id",'=',values['wallet_id'])],limit=1)
            if wallet:
                saldo=values['amount']
                if (wallet.amount<=saldo):
                    cliente=self.env['res.partner'].search([("id",'=',values['partner_id'])],limit=1)
                    cliente.property_product_pricelist=1
