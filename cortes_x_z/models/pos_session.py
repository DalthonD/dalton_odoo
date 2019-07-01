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

import logging
from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from pytz import timezone
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo import exceptions
_logger = logging.getLogger(__name__)


class pos_session(models.Model):
    _inherit = "pos.session"

    @api.multi
    def get_pos_name(self):
        if self and self.config_id:
            return self.config_id.name

    @api.multi
    def get_inventory_details(self):
        product_category = self.env['product.category'].search([])
        product_product = self.env['product.product']
        stock_location = self.config_id.stock_location_id;
        inventory_records = []
        final_list = []
        product_details = []
        if self and self.id:
            for order in self.order_ids:
                for line in order.lines:
                    product_details.append({
                        'id': line.product_id.id,
                        'qty': line.qty,
                    })
        custom_list = []
        for each_prod in product_details:
            if each_prod.get('id') not in [x.get('id') for x in custom_list]:
                custom_list.append(each_prod)
            else:
                for each in custom_list:
                    if each.get('id') == each_prod.get('id'):
                        each.update({'qty': each.get('qty') + each_prod.get('qty')})
        for each in custom_list:
            product_id = product_product.browse(each.get('id'))
            if product_id:
                inventory_records.append({
                    'product_id': [product_id.id, product_id.name],
                    'category_id': [product_id.id, product_id.categ_id.name],
                    'used_qty': each.get('qty'),
                    'quantity': product_id.with_context(
                        {'location': stock_location.id, 'compute_child': False}).qty_available,
                    'uom_name': product_id.uom_id.name or ''
                })
            if inventory_records:
                temp_list = []
                temp_obj = []
                for each in inventory_records:
                    if each.get('product_id')[0] not in temp_list:
                        temp_list.append(each.get('product_id')[0])
                        temp_obj.append(each)
                    else:
                        for rec in temp_obj:
                            if rec.get('product_id')[0] == each.get('product_id')[0]:
                                qty = rec.get('quantity') + each.get('quantity')
                                rec.update({'quantity': qty})
                final_list = sorted(temp_obj, key=lambda k: k['quantity'])
        return final_list or []

    @api.multi
    def get_proxy_ip(self):
        proxy_id = self.env['res.users'].browse([self._uid]).company_id.report_ip_address
        return {'ip': proxy_id or False}

    @api.multi
    def get_user(self):
        if self._uid == SUPERUSER_ID:
            return True

    @api.multi
    def get_gross_total(self):
        gross_total = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    gross_total += line.qty * (line.price_unit - line.product_id.standard_price)
        return gross_total

    @api.multi
    def get_product_cate_total(self):
        balance_end_real = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    balance_end_real += (line.qty * line.price_unit)
        return balance_end_real

    @api.multi
    def get_net_gross_total(self):
        net_gross_profit = 0.0
        if self:
            net_gross_profit = self.get_gross_total() - self.get_total_tax()
        return net_gross_profit

    @api.multi
    def get_product_name(self, category_id):
        if category_id:
            category_name = self.env['pos.category'].browse([category_id]).name
            return category_name

    @api.multi
    def get_payments(self):
        if self:
            statement_line_obj = self.env["account.bank.statement.line"]
            pos_order_obj = self.env["pos.order"]
            company_id = self.env['res.users'].browse([self._uid]).company_id.id
            pos_ids = pos_order_obj.search([('state','in',['paid','invoiced','done']),
                                            ('company_id', '=', company_id),('session_id','=',self.id)])
            data={}
            if pos_ids:
                pos_ids = [pos.id for pos in pos_ids]
                st_line_ids = statement_line_obj.search([('pos_statement_id', 'in', pos_ids)])
                if st_line_ids:
                    a_l=[]
                    for r in st_line_ids:
                        a_l.append(r['id'])
                    self._cr.execute("select aj.name,sum(amount) from account_bank_statement_line as absl,account_bank_statement as abs,account_journal as aj " \
                                    "where absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
                                    "group by aj.name ",(tuple(a_l),))

                    data = self._cr.dictfetchall()
                    return data
            else:
                return {}

    @api.multi
    def get_product_category(self):
        product_list = []
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    flag = False
                    product_dict = {}
                    for lst in product_list:
                        if line.product_id.pos_categ_id:
                            if lst.get('pos_categ_id') == line.product_id.pos_categ_id.id:
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                        else:
                            if lst.get('pos_categ_id') == '':
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                    if not flag:
                        product_dict.update({
                                    'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                                    'price': (line.qty * line.price_unit)
                                })
                        product_list.append(product_dict)
        return product_list

    @api.multi
    def get_journal_amount(self):
        journal_list = []
        if self and self.statement_ids:
            for statement in self.statement_ids:
                journal_dict = {}
                journal_dict.update({'journal_id': statement.journal_id and statement.journal_id.name or '',
                                     'ending_bal': statement.balance_end_real or 0.0})
                journal_list.append(journal_dict)
        return journal_list

    @api.multi
    def get_total_closing(self):
        if self:
            return self.cash_register_balance_end_real

    @api.multi
    def get_total_sales(self):
        total_price = 0.0
        if self:
            for order in self.order_ids:
                total_price += sum([(line.qty * line.price_unit) for line in order.lines])
        return total_price

    @api.multi
    def get_total_tax(self):
        if self:
            total_tax = 0.0
            pos_order_obj = self.env['pos.order']
            total_tax += sum([order.amount_tax for order in pos_order_obj.search([('session_id', '=', self.id)])])
        return total_tax

    @api.multi
    def get_vat_tax(self):
        taxes_info = []
        if self:
            tax_list = []
            tax_list = [tax.id for order in self.order_ids for line in order.lines.filtered(lambda line: line.tax_ids_after_fiscal_position) for tax in line.tax_ids_after_fiscal_position]
            tax_list = list(set(tax_list))
            for tax in self.env['account.tax'].browse(tax_list):
                total_tax = 0.00
                net_total = 0.00
                for line in self.env['pos.order.line'].search([('order_id', 'in', [order.id for order in self.order_ids])]).filtered(lambda line: tax in line.tax_ids_after_fiscal_position ):
                    total_tax += line.price_subtotal * tax.amount / 100
                    net_total += line.price_subtotal
                taxes_info.append({
                    'tax_name': tax.name,
                    'tax_total': total_tax,
                    'tax_per': tax.amount,
                    'net_total': net_total,
                    'gross_tax': total_tax + net_total
                })
        return taxes_info

    @api.multi
    def get_total_discount(self):
        total_discount = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                total_discount += sum([((line.qty * line.price_unit) * line.discount) / 100 for line in order.lines])
        return total_discount

    @api.multi
    def get_total_first(self):
        total = 0.0
        if self:
            total = (self.get_total_sales() + self.get_total_tax())\
                - (abs(self.get_total_discount()))
        return total

    @api.multi
    def get_session_date(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = timezone(self._context.get('tz'))
            else:
                tz = pytz.utc
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            if sign == '+':
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) + \
                                                    timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) - \
                                                    timedelta(hours=hour_tz, minutes=min_tz)
            return date_time.strftime('%d/%m/%Y')

    @api.multi
    def get_session_time(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = timezone(self._context.get('tz'))
            else:
                tz = pytz.utc
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            if sign == '+':
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) + \
                                                    timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) - \
                                                    timedelta(hours=hour_tz, minutes=min_tz)
            return date_time.strftime('%I:%M:%S %p')

    @api.multi
    def get_current_date(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')

    @api.multi
    def get_current_time(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')
# X - Report
    @api.multi
    def get_company_data_x(self):
        return self.user_id.company_id

    @api.multi
    def get_current_date_x(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')

    @api.multi
    def get_session_date_x(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = self._context['tz']
                tz = timezone(tz)
            else:
                tz = pytz.utc
            if tz:
                c_time = datetime.now(tz)
                hour_tz = int(str(c_time)[-5:][:2])
                min_tz = int(str(c_time)[-5:][3:])
                sign = str(c_time)[-6][:1]
                if sign == '+':
                    date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) + \
                                                        timedelta(hours=hour_tz, minutes=min_tz)
                else:
                    date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) - \
                                                        timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT)
            return date_time

    @api.multi
    def get_current_time_x(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')

    @api.multi
    def get_session_time_x(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = self._context['tz']
                tz = timezone(tz)
            else:
                tz = pytz.utc
            if tz:
                c_time = datetime.now(tz)
                hour_tz = int(str(c_time)[-5:][:2])
                min_tz = int(str(c_time)[-5:][3:])
                sign = str(c_time)[-6][:1]
                if sign == '+':
                    date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) + \
                                                        timedelta(hours=hour_tz, minutes=min_tz)
                else:
                    date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) - \
                                                        timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT)
            return date_time.strftime('%I:%M:%S %p')

    @api.multi
    def get_total_sales_x(self):
        total_price = 0.0
        if self:
            for order in self.order_ids:
                    for line in order.lines:
                            total_price += (line.qty * line.price_unit)
        return total_price

    @api.multi
    def get_total_returns_x(self):
        pos_order_obj = self.env['pos.order']
        total_return = 0.0
        if self:
            for order in pos_order_obj.search([('session_id', '=', self.id)]):
                if order.amount_total < 0:
                    total_return += abs(order.amount_total)
        return total_return

    @api.multi
    def get_total_tax_x(self):
        total_tax = 0.0
        if self:
            pos_order_obj = self.env['pos.order']
            total_tax += sum([order.amount_tax for order in pos_order_obj.search([('session_id', '=', self.id)])])
        return total_tax

    @api.multi
    def get_total_discount_x(self):
        total_discount = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                total_discount += sum([((line.qty * line.price_unit) * line.discount) / 100 for line in order.lines])
        return total_discount

    @api.multi
    def get_total_first_x(self):
        global gross_total
        if self:
            gross_total = (self.get_total_sales() + self.get_total_tax()) \
                 + self.get_total_discount()
        return gross_total

    @api.multi
    def get_user_x(self):
        if self._uid == SUPERUSER_ID:
            return True

    @api.multi
    def get_gross_total_x(self):
        total_cost = 0.0
        gross_total = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    total_cost += line.qty * line.product_id.standard_price
        gross_total = self.get_total_sales() - \
                    + self.get_total_tax() - total_cost
        return gross_total

    @api.multi
    def get_product_cate_total_x(self):
        balance_end_real = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    balance_end_real += (line.qty * line.price_unit)
        return balance_end_real

    @api.multi
    def get_net_gross_total_x(self):
        net_gross_profit = 0.0
        total_cost = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    total_cost += line.qty * line.product_id.standard_price
            net_gross_profit = self.get_total_sales() - self.get_total_tax() - total_cost
        return net_gross_profit

    @api.multi
    def get_product_name_x(self, category_id):
        if category_id:
            category_name = self.env['pos.category'].browse([category_id]).name
            return category_name

    @api.multi
    def get_product_category_x(self):
        product_list = []
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    flag = False
                    product_dict = {}
                    for lst in product_list:
                        if line.product_id.pos_categ_id:
                            if lst.get('pos_categ_id') == line.product_id.pos_categ_id.id:
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                lst['qty'] = lst.get('qty') or 0.0 + line.qty
                                flag = True
                        else:
                            if lst.get('pos_categ_id') == '':
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                lst['qty'] = lst.get('qty') or 0.0 + line.qty
                                flag = True
                    if not flag:
                        if line.product_id.pos_categ_id:
                            product_dict.update({
                                        'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                                        'price': (line.qty * line.price_unit),
                                        'qty': line.qty
                                    })
                        else:
                            product_dict.update({
                                        'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                                        'price': (line.qty * line.price_unit),
                                    })
                        product_list.append(product_dict)
        return product_list

    @api.multi
    def get_payments_x(self):
        if self:
            statement_line_obj = self.env["account.bank.statement.line"]
            pos_order_obj = self.env["pos.order"]
            company_id = self.env['res.users'].browse([self._uid]).company_id.id
            pos_ids = pos_order_obj.search([('session_id', '=', self.id),
                                            ('state', 'in', ['paid', 'invoiced', 'done']),
                                            ('user_id', '=', self.user_id.id), ('company_id', '=', company_id)])
            data = {}
            if pos_ids:
                pos_ids = [pos.id for pos in pos_ids]
                st_line_ids = statement_line_obj.search([('pos_statement_id', 'in', pos_ids)])
                if st_line_ids:
                    a_l = []
                    for r in st_line_ids:
                        a_l.append(r['id'])
                    self._cr.execute("select aj.name,sum(amount) from account_bank_statement_line as absl,account_bank_statement as abs,account_journal as aj " \
                                    "where absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
                                    "group by aj.name ", (tuple(a_l),))

                    data = self._cr.dictfetchall()
                    return data
            else:
                return {}

    @api.multi
    def get_payments_invoice(self):
        if self:
            start_at = self.start_at
            stop_at = datetime.now()
            if self.stop_at:
                stop_at = self.stop_at
            account_payment_obj = self.env["account.payment"]
            invoice_obj = self.env["account.invoice"]
            #journal_obj = self.env["account.journal"]
            company_id = self.env['res.users'].browse([self._uid]).company_id.id
            inv_ids = invoice_obj.search([('create_date', '>=', start_at),
                                            ('create_date', '<=', stop_at),
                                            ('state', '=', 'paid'),
                                            ('user_id', '=', self.user_id.id), ('company_id', '=', company_id)])
            data = {}
            if inv_ids:
                inv_ids = [inv.partner_id.id for inv in inv_ids]
                account_payment_ids = account_payment_obj.search([('partner_id', 'in', inv_ids),('payment_date', '>=', start_at),
                                                ('payment_date', '<=', stop_at),
                                                ('create_uid', '=', self.user_id.id), ('company_id', '=', company_id)])
                if account_payment_ids:
                    a_l = []
                    for r in account_payment_ids:
                        a_l.append(r['id'])
                    self._cr.execute("select aj.name, sum(ap.amount) from account_payment as ap, account_journal as aj " \
                                    "where ap.journal_id = aj.id  and ap.id IN %s " \
                                    "group by aj.name ", (tuple(a_l),))
                    data = self._cr.dictfetchall()
                    return data
        else:
            return {}

    ########FACTURA CORTE X##############
    @api.multi
    def get_invoice_range_no_contr(self):
        invran = '0-0'
        if self:
            for record in self:
                start_at = record.start_at
                stop_at = datetime.now()
                if record.stop_at:
                    stop_at = record.stop_at
                invoices = []
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False)])
                pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','in',['paid','open']),('fiscal_position_id','!=',False)\
                ,('create_date','>=',start_at),('create_date','<=',stop_at)], order='reference asc')
                if len(fiscal_position_ids)>1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id in fiscal_position_ids:
                            invoices.append(inv)
                elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id == fiscal_position_ids:
                            invoices.append(inv)
                else:
                    return invran
                if len(invoices)>1:
                    inv_in = invoices[0].reference
                    inv_fin = invoices[-1].reference
                elif len(invoices)==1:
                    inv_in = invoices[0].reference
                    inv_fin = '(único)'
                else:
                    inv_in = 0
                    inv_fin = 0
                invran = '{0}-{1}'.format(inv_in,inv_fin)
                return invran
        else:
            return invran

    @api.multi
    def get_total_sales_invoice_gravado_no_contr(self):
        total_price = 0.0
        if self:
            for record in self:
                start_at = record.start_at
                stop_at = datetime.now()
                if record.stop_at:
                    stop_at = record.stop_at
                #pos_order_obj = []
                #sales_invoice = []
                invoices = []
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','Gravado')])
                pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','in',['paid','open']),('fiscal_position_id','!=',False)\
                ,('create_date','>=',start_at),('create_date','<=',stop_at)], order='reference asc')
                #sql = "select invoice_id from pos_order where invoice_id IS NOT NULL and session_id = {0} order by invoice_id asc".format(record.id)
                #self._cr.execute(sql)
                #pos_order_obj = self._cr.dictfetchall()
                #for order in pos_order_obj:
                #    for invoice in sales_invoice:
                #        if order.get('invoice_id')==invoice.id:
                #            pos_invoice_obj.append(invoice)
                if len(fiscal_position_ids)>1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id in fiscal_position_ids:
                            invoices.append(inv)
                elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id == fiscal_position_ids:
                            invoices.append(inv)
                else:
                    return total_price
                for inv in invoices:
                    total_price += inv.amount_total
                return total_price
        else:
            return total_price

    @api.multi
    def get_total_sales_invoice_exento_no_contr(self):
        total_price = 0.0
        if self:
            for record in self:
                start_at = record.start_at
                stop_at = datetime.now()
                if record.stop_at:
                    stop_at = record.stop_at
                #pos_order_obj = []
                #sales_invoice = []
                invoices = []
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','Exento')])
                pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','in',['paid','open']),('fiscal_position_id','!=',False)\
                ,('create_date','>=',start_at),('create_date','<=',stop_at)], order='reference asc')
                #sql = "select invoice_id from pos_order where invoice_id IS NOT NULL and session_id = {0} order by invoice_id asc".format(record.id)
                #self._cr.execute(sql)
                #pos_order_obj = self._cr.dictfetchall()
                #for order in pos_order_obj:
                #    for invoice in sales_invoice:
                #        if order.get('invoice_id')==invoice.id:
                #            pos_invoice_obj.append(invoice)
                if len(fiscal_position_ids)>1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id in fiscal_position_ids:
                            invoices.append(inv)
                elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id == fiscal_position_ids:
                            invoices.append(inv)
                else:
                    return total_price
                for inv in invoices:
                    total_price += inv.amount_total
                return total_price
        else:
            return total_price

    @api.multi
    def get_total_sales_invoice_no_aplica_no_contr(self):
        total_price = 0.0
        if self:
            for record in self:
                start_at = record.start_at
                stop_at = datetime.now()
                if record.stop_at:
                    stop_at = record.stop_at
                #pos_order_obj = []
                #sales_invoice = []
                invoices = []
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','No Aplica')])
                pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','in',['paid','open']),('fiscal_position_id','!=',False)\
                ,('create_date','>=',start_at),('create_date','<=',stop_at)], order='reference asc')
                #sql = "select invoice_id from pos_order where invoice_id IS NOT NULL and session_id = {0} order by invoice_id asc".format(record.id)
                #self._cr.execute(sql)
                #pos_order_obj = self._cr.dictfetchall()
                #for order in pos_order_obj:
                #    for invoice in sales_invoice:
                #        if order.get('invoice_id')==invoice.id:
                #            pos_invoice_obj.append(invoice)
                if len(fiscal_position_ids)>1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id in fiscal_position_ids:
                            invoices.append(inv)
                elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id == fiscal_position_ids:
                            invoices.append(inv)
                else:
                    return total_price
                for inv in invoices:
                    total_price += inv.amount_total
                return total_price
        else:
            return total_price
    #############################

    ########CCF CORTE X##############

    @api.multi
    def get_invoice_range_ccf(self):
        invran = '0-0'
        if self:
            for record in self:
                start_at = record.start_at
                stop_at = datetime.now()
                if record.stop_at:
                    stop_at = record.stop_at
                #pos_order_obj = []
                #sales_invoice = []
                invoices = []
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',True)])
                pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','in',['paid','open']),('fiscal_position_id','!=',False)\
                ,('create_date','>=',start_at),('create_date','<=',stop_at),('sv_credito_fiscal','=',True)], order='reference asc')
                #sql = "select invoice_id from pos_order where invoice_id IS NOT NULL and session_id = {0} order by invoice_id asc".format(record.id)
                #self._cr.execute(sql)
                #pos_order_obj = self._cr.dictfetchall()
                #for order in pos_order_obj:
                    #for invoice in sales_invoice:
                        #if order.get('invoice_id')==invoice.id:
                            #pos_invoice_obj.append(invoice)
                #pos_invoice_obj.sort(key=lambda i: i.reference)
                if len(fiscal_position_ids)>1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id in fiscal_position_ids:
                            invoices.append(inv)
                elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id == fiscal_position_ids:
                            invoices.append(inv)
                else:
                    return invran
                if len(invoices)>1:
                    inv_in = invoices[0].reference
                    inv_fin = invoices[-1].reference
                elif len(invoices)==1:
                    inv_in = invoices[0].reference
                    inv_fin = '(único)'
                else:
                    inv_in = 0
                    inv_fin = 0
                invran = '{0}-{1}'.format(inv_in,inv_fin)
                return invran
        else:
            return invran

    @api.multi
    def get_total_sales_invoice_gravado_ccf(self):
        total_price = 0.0
        if self:
            for record in self:
                start_at = record.start_at
                stop_at = datetime.now()
                if record.stop_at:
                    stop_at = record.stop_at
                #pos_order_obj = []
                #sales_invoice = []
                invoices = []
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',True),('sv_clase','=','Gravado')])
                pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','!=','cancel'),('fiscal_position_id','!=',False)\
                ,('create_date','>=',start_at),('create_date','<=',stop_at),('sv_credito_fiscal','=',True)], order='reference asc')
                #sql = "select invoice_id from pos_order where invoice_id IS NOT NULL and session_id = {0} order by invoice_id asc".format(record.id)
                #self._cr.execute(sql)
                #pos_order_obj = self._cr.dictfetchall()
                #for order in pos_order_obj:
                #    for invoice in sales_invoice:
                #        if order.get('invoice_id')==invoice.id:
                #            pos_invoice_obj.append(invoice)
                if len(fiscal_position_ids)>1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id in fiscal_position_ids:
                            invoices.append(inv)
                elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id == fiscal_position_ids:
                            invoices.append(inv)
                else:
                    return total_price
                for inv in invoices:
                    total_price += inv.amount_total
                return total_price
        else:
            return total_price

    @api.multi
    def get_total_sales_invoice_exento_ccf(self):
        total_price = 0.0
        if self:
            for record in self:
                start_at = record.start_at
                stop_at = datetime.now()
                if record.stop_at:
                    stop_at = record.stop_at
                #pos_order_obj = []
                #sales_invoice = []
                invoices = []
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',True),('sv_clase','=','Exento')])
                pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','!=','cancel'),('fiscal_position_id','!=',False)\
                ,('create_date','>=',start_at),('create_date','<=',stop_at),('sv_credito_fiscal','=',True)], order='reference asc')
                #sql = "select invoice_id from pos_order where invoice_id IS NOT NULL and session_id = {0} order by invoice_id asc".format(record.id)
                #self._cr.execute(sql)
                #pos_order_obj = self._cr.dictfetchall()
                #for order in pos_order_obj:
                #    for invoice in sales_invoice:
                #        if order.get('invoice_id')==invoice.id:
                #            pos_invoice_obj.append(invoice)
                if len(fiscal_position_ids)>1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id in fiscal_position_ids:
                            invoices.append(inv)
                elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id == fiscal_position_ids:
                            invoices.append(inv)
                else:
                    return total_price
                for inv in invoices:
                    total_price += inv.amount_total
                return total_price
        else:
            return total_price

    @api.multi
    def get_total_sales_invoice_no_aplica_ccf(self):
        total_price = 0.0
        if self:
            for record in self:
                start_at = record.start_at
                stop_at = datetime.now()
                if record.stop_at:
                    stop_at = record.stop_at
                #pos_order_obj = []
                #sales_invoice = []
                invoices = []
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',True),('sv_clase','=','No Aplica')])
                pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','!=','cancel'),('fiscal_position_id','!=',False)\
                ,('create_date','>=',start_at),('create_date','<=',stop_at),('sv_credito_fiscal','=',True)], order='reference asc')
                #sql = "select invoice_id from pos_order where invoice_id IS NOT NULL and session_id = {0} order by invoice_id asc".format(record.id)
                #self._cr.execute(sql)
                #pos_order_obj = self._cr.dictfetchall()
                #for order in pos_order_obj:
                #    for invoice in sales_invoice:
                #        if order.get('invoice_id')==invoice.id:
                #            pos_invoice_obj.append(invoice)
                if len(fiscal_position_ids)>1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id in fiscal_position_ids:
                            invoices.append(inv)
                elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                    for inv in pos_invoice_obj:
                        if inv.fiscal_position_id == fiscal_position_ids:
                            invoices.append(inv)
                else:
                    return total_price
                for inv in invoices:
                    total_price += inv.amount_total
                return total_price
        else:
            return total_price
    ############################

    #############TIQUETE CORTE X#############
    @api.multi
    def get_ticket_range(self):
        tcktran = '0-0'
        if self:
            for record in self:
                pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',record.id),('recibo_number','=',False),('ticket_number','!=',False)], order='ticket_number asc')
                if len(pos_order_obj)>1:
                    tckt_in = pos_order_obj[0].ticket_number
                    tckt_fin = pos_order_obj[-1].ticket_number
                elif len(pos_order_obj)==1:
                    tckt_in = pos_order_obj[0].ticket_number
                    tckt_fin = '(único)'
                else:
                    tckt_in = 0
                    tckt_fin = 0
                tcktran = '{0}-{1}'.format(tckt_in,tckt_fin)
                return tcktran
        return tcktran

    @api.multi
    def get_total_sales_ticket_gravado(self):
        total_price = 0.0
        if self:
            for record in self:
                pos_order_obj = []
                orders = []
                #fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','Gravado')])
                default_fiscal_position_id = record.config_id.default_fiscal_position_id
                pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',record.id),('recibo_number','=',False),('ticket_number','!=',False)], order='ticket_number asc')
                if pos_order_obj:
                    for order in pos_order_obj:
                        if order.fiscal_position_id == default_fiscal_position_id:
                            orders.append(order)
                else:
                    return total_price
                for order in orders:
                    total_price += sum([(line.qty * line.price_unit) for line in order.lines])
                return total_price
        else:
            return total_price

    @api.multi
    def get_total_sales_ticket_exento(self):
        total_price = 0.0
        if self:
            for record in self:
                pos_order_obj = []
                orders = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','Exento')])
                pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',record.id),('recibo_number','=',False),('ticket_number','!=',False)], order='ticket_number asc')
                if len(fiscal_position_ids)>1 and pos_order_obj:
                    for order in pos_order_obj:
                        if order.fiscal_position_id in fiscal_position_ids:
                            orders.append(order)
                elif len(fiscal_position_ids)==1 and pos_order_obj:
                    for order in pos_order_obj:
                        if order.fiscal_position_id == fiscal_position_ids:
                            orders.append(order)
                else:
                    return total_price
                for order in orders:
                    total_price += sum([(line.qty * line.price_unit) for line in order.lines])
                return total_price
        else:
            return total_price

    @api.multi
    def get_total_sales_ticket_no_aplica(self):
        total_price = 0.0
        if self:
            for record in self:
                pos_order_obj = []
                orders = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','No Aplica')])
                pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',record.id),('recibo_number','=',False),('ticket_number','!=',False)], order='ticket_number asc')
                if len(fiscal_position_ids)>1 and pos_order_obj:
                    for order in pos_order_obj:
                        if order.fiscal_position_id in fiscal_position_ids:
                            orders.append(order)
                elif len(fiscal_position_ids)==1 and pos_order_obj:
                    for order in pos_order_obj:
                        if order.fiscal_position_id == fiscal_position_ids:
                            orders.append(order)
                else:
                    return total_price
                for order in orders:
                    total_price += sum([(line.qty * line.price_unit) for line in order.lines])
                return total_price
        else:
            return total_price

    @api.multi
    def get_total_sales_tickets(self):
        total_price = 0.0
        if self:
            for record in self:
                pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',record.id),('recibo_number','=',False),('ticket_number','!=',False)], order='ticket_number asc')
                if pos_order_obj:
                    for order in pos_order_obj:
                        total_price += sum([(line.qty * line.price_unit) for line in order.lines])
                    return total_price
                else:
                    return total_price
        return total_price

    @api.multi
    def get_total_returns_tickets_x(self):
        total_return = 0.0
        if self:
            for record in self:
                for order in self.env['pos.order'].search([('session_id', '=', record.id),('invoice_id','=',False),('recibo_number','=',False),('ticket_number','!=',False)]):
                    if order.amount_total < 0:
                        total_return += abs(order.amount_total)
        return total_return

    ############################

    #############RECIBO WALLET CORTE X#############
    @api.multi
    def get_wallet_reciept(self):
        recran = '0-0'
        if self:
            for record in self:
                pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',record.id), ('recibo_number','!=',False),('ticket_number','=',False)], order='recibo_number asc')
                if len(pos_order_obj)>1:
                    rec_in = pos_order_obj[0].recibo_number
                    rec_fin = pos_order_obj[-1].recibo_number
                elif len(pos_order_obj)==1:
                    rec_in = pos_order_obj[0].recibo_number
                    rec_fin = '(único)'
                else:
                    rec_in = 0
                    rec_fin = 0
                recran = '{0}-{1}'.format(rec_in,rec_fin)
                return recran
        else:
            return recran

    @api.multi
    def get_total_wallet_recharges(self):
        total_price = 0.0
        if self:
            for record in self:
                pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',record.id),('recibo_number','!=',False),('ticket_number','=',False)], order='recibo_number asc')
                if pos_order_obj:
                    for order in pos_order_obj:
                        total_price += sum([(line.qty * line.price_unit) for line in order.lines])
                    return total_price
                else:
                    return total_price
        return total_price

    ############################

class pos_config(models.Model):
    _inherit = 'pos.config'

    @api.multi
    def get_invoice_range_no_contr_z(self, today):
        session_ids = []
        invoices = set()
        invran = '0-0'
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        hora = time(20,0,0)
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False)])
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        start_at = session.start_at
                        stop_at = session.stop_at
                        pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','in',['paid','open']),('fiscal_position_id','!=',False)\
                        ,('create_date','>=',start_at),('create_date','<=',stop_at)], order='reference asc')
                        if len(fiscal_position_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_ids:
                                    invoices.add(inv)
                        elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_ids:
                                    invoices.add(inv)
                        else:
                            continue
                    invoices = list(invoices)
                    invoices.sort(key=lambda i: i.reference)
                    if invoices:
                        if len(invoices)>1:
                            inv_in = invoices[0].reference
                            inv_fin = invoices[-1].reference
                        elif len(invoices)==1:
                            inv_in = invoices[0].reference
                            inv_fin = '(único)'
                        else:
                            inv_in = 0
                            inv_fin = 0
                        invran = '{0}-{1}'.format(inv_in,inv_fin)
                        return invran
                    return invran
                return invran
        return invran

    @api.multi
    def get_invoice_info_z(self, today):
        session_ids = []
        invoices = set()
        invran = '0-0'
        gravado = 0.0
        excento = 0.0
        no_aplica= 0.0
        total_price = 0.0
        data = {"invran":invran,"gravado":gravado,"excento":excento,"no_aplica":no_aplica,"total_price":total_price}
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False)])
                fiscal_position_gravado_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','Gravado')])
                fiscal_position_excento_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','Exento')])
                fiscal_position_noaplica_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','No Aplica')])
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        start_at = session.start_at
                        stop_at = session.stop_at
                        pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','in',['paid','open']),('fiscal_position_id','!=',False)\
                        ,('create_date','>=',start_at),('create_date','<=',stop_at)], order='reference asc')
                        if len(fiscal_position_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_ids:
                                    invoices.add(inv)
                        elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_ids:
                                    invoices.add(inv)
                        else:
                            continue
                    invoices = list(invoices)
                    invoices.sort(key=lambda i: i.reference)
                    if invoices:
                        if len(invoices)>1:
                            inv_in = invoices[0].reference
                            inv_fin = invoices[-1].reference
                        elif len(invoices)==1:
                            inv_in = invoices[0].reference
                            inv_fin = '(único)'
                        else:
                            inv_in = 0
                            inv_fin = 0
                        invran = '{0}-{1}'.format(inv_in,inv_fin)
                        data["invran"]=invran #rango de facturas del POS
                        pos_invoice_obj = invoices #Listado de todos las facturas hechas en las sessiones del POS
                        invoices = []
                        if len(fiscal_position_gravado_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_gravado_ids:
                                    invoices.append(inv)
                        elif len(fiscal_position_gravado_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_gravado_ids:
                                    invoices.append(inv)
                        else:
                            gravado = 0.0 #En caso no haya facturas gravadas
                        if invoices:
                            for inv in invoices:
                                gravado += inv.amount_total
                        data["gravado"] = gravado #Facturas gravadas
                        invoices = []
                        if len(fiscal_position_excento_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_excento_ids:
                                    invoices.append(inv)
                        elif len(fiscal_position_excento_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_excento_ids:
                                    invoices.append(inv)
                        else:
                            excento = 0.0 #En caso no haya facturas gravadas
                        if invoices:
                            for inv in invoices:
                                excento += inv.amount_total
                        data["excento"] = excento
                        invoices = []
                        if len(fiscal_position_noaplica_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_noaplica_ids:
                                    invoices.append(inv)
                        elif len(fiscal_position_noaplica_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_noaplica_ids:
                                    invoices.append(inv)
                        else:
                            no_aplica = 0.0 #En caso no haya facturas gravadas
                        if invoices:
                            for inv in invoices:
                                no_aplica += inv.amount_total
                        data["no_aplica"] = no_aplica
                        data["total_price"] = total_price + gravado + excento + no_aplica
                        return data
                    return data
                return data
        return data

    @api.multi
    def get_ccf_info_z(self, today):
        session_ids = []
        invoices = set()
        invran = '0-0'
        gravado = 0.0
        excento = 0.0
        no_aplica= 0.0
        total_price = 0.0
        data = {"invran":invran,"gravado":gravado,"excento":excento,"no_aplica":no_aplica,"total_price":total_price}
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_invoice_obj = []
                fiscal_position_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',True)])
                fiscal_position_gravado_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',True),('sv_clase','=','Gravado')])
                fiscal_position_excento_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',True),('sv_clase','=','Exento')])
                fiscal_position_noaplica_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',True),('sv_clase','=','No Aplica')])
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        start_at = session.start_at
                        stop_at = session.stop_at
                        pos_invoice_obj = self.env['account.invoice'].search([('reference','!=',False),('state','in',['paid','open']),('fiscal_position_id','!=',False)\
                        ,('create_date','>=',start_at),('create_date','<=',stop_at)], order='reference asc')
                        if len(fiscal_position_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_ids:
                                    invoices.add(inv)
                        elif len(fiscal_position_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_ids:
                                    invoices.add(inv)
                        else:
                            continue
                    invoices = list(invoices)
                    invoices.sort(key=lambda i: i.reference)
                    if invoices:
                        if len(invoices)>1:
                            inv_in = invoices[0].reference
                            inv_fin = invoices[-1].reference
                        elif len(invoices)==1:
                            inv_in = invoices[0].reference
                            inv_fin = '(único)'
                        else:
                            inv_in = 0
                            inv_fin = 0
                        invran = '{0}-{1}'.format(inv_in,inv_fin)
                        data["invran"]=invran #rango de facturas del POS
                        pos_invoice_obj = invoices #Listado de todos las facturas hechas en las sessiones del POS
                        invoices = []
                        if len(fiscal_position_gravado_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_gravado_ids:
                                    invoices.append(inv)
                        elif len(fiscal_position_gravado_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_gravado_ids:
                                    invoices.append(inv)
                        else:
                            gravado = 0.0 #En caso no haya facturas gravadas
                        if invoices:
                            for inv in invoices:
                                gravado += inv.amount_total
                        data["gravado"] = gravado #Facturas gravadas
                        invoices = []
                        if len(fiscal_position_excento_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_excento_ids:
                                    invoices.append(inv)
                        elif len(fiscal_position_excento_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_excento_ids:
                                    invoices.append(inv)
                        else:
                            excento = 0.0 #En caso no haya facturas gravadas
                        if invoices:
                            for inv in invoices:
                                excento += inv.amount_total
                        data["excento"] = excento
                        invoices = []
                        if len(fiscal_position_noaplica_ids)>1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id in fiscal_position_noaplica_ids:
                                    invoices.append(inv)
                        elif len(fiscal_position_noaplica_ids)==1 and pos_invoice_obj:
                            for inv in pos_invoice_obj:
                                if inv.fiscal_position_id == fiscal_position_noaplica_ids:
                                    invoices.append(inv)
                        else:
                            no_aplica = 0.0 #En caso no haya facturas gravadas
                        if invoices:
                            for inv in invoices:
                                no_aplica += inv.amount_total
                        data["no_aplica"] = no_aplica
                        data["total_price"] = total_price + gravado + excento + no_aplica
                        return data
                    return data
                return data
        return data

    @api.multi
    def get_tiquete_info_z(self, today):
        session_ids = []
        orders = set()
        tcktran = '0-0'
        gravado = 0.0
        excento = 0.0
        no_aplica= 0.0
        total_price = 0.0
        data = {"tcktran":tcktran,"gravado":gravado,"excento":excento,"no_aplica":no_aplica,"total_price":total_price}
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_order_obj = []
                #fiscal_position_gravado_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','Gravado')])
                default_fiscal_position_id = pos.default_fiscal_position_id #No contribuyente gravado local
                fiscal_position_excento_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','Exento')])
                fiscal_position_noaplica_ids = self.env['account.fiscal.position'].search([('sv_contribuyente','=',False),('sv_clase','=','No Aplica')])
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',session.id),('recibo_number','=',False),('ticket_number','!=',False)], order='ticket_number asc')
                        for order in pos_order_obj:
                            orders.add(order)
                    orders = list(orders)
                    orders.sort(key=lambda o: o.ticket_number)
                    if orders:
                        if len(orders)>1:
                            tckt_in = orders[0].ticket_number
                            tckt_fin = orders[-1].ticket_number
                        elif len(orders)==1:
                            tckt_in = orders[0].ticket_number
                            tckt_fin = '(único)'
                        else:
                            tckt_in = 0
                            tckt_fin = 0
                        tcktran = '{0}-{1}'.format(tckt_in,tckt_fin)
                        data["tcktran"]=tcktran #rango de tickets del POS
                        pos_order_obj = orders #Listado de todos las ordenes hechas en las sessiones del POS
                        orders = [] #Nos aseguramos que la lista esté vacía
                        for order in pos_order_obj:
                            if order.fiscal_position_id == default_fiscal_position_id:
                                orders.append(order)
                        if orders:
                            for order in orders:
                                gravado += sum([(line.qty * line.price_unit) for line in order.lines])
                        data["gravado"] = gravado #Facturas gravadas
                        orders = [] #volvemos a vaciar las ordernes
                        if len(fiscal_position_excento_ids)>1 and pos_order_obj:
                            for order in pos_order_obj:
                                if order.fiscal_position_id in fiscal_position_excento_ids:
                                    orders.append(order)
                        elif len(fiscal_position_excento_ids)==1 and pos_order_obj:
                            for order in pos_order_obj:
                                if order.fiscal_position_id == fiscal_position_excento_ids:
                                    orders.append(order)
                        else:
                            excento = 0.0 #En caso no haya ordernes excentas
                        if orders:
                            for order in orders:
                                excento += sum([(line.qty * line.price_unit) for line in order.lines])
                        data["excento"] = excento
                        orders = []
                        if len(fiscal_position_noaplica_ids)>1 and pos_order_obj:
                            for order in pos_order_obj:
                                if order.fiscal_position_id in fiscal_position_ids:
                                    orders.append(order)
                        elif len(fiscal_position_noaplica_ids)==1 and pos_order_obj:
                            for order in pos_order_obj:
                                if order.fiscal_position_id == fiscal_position_noaplica_ids:
                                    orders.append(order)
                        else:
                            no_aplica = 0.0 #En caso no haya facturas gravadas
                        if orders:
                            for order in orders:
                                no_aplica += sum([(line.qty * line.price_unit) for line in order.lines])
                        data["no_aplica"] = no_aplica
                        data["total_price"] = total_price + gravado + excento + no_aplica
                        return data
                    return data
                return data
        return data

    @api.multi
    def get_total_sales_tickets_z(self, today):
        session_ids = []
        total_price = 0.0
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_order_obj = []
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        total_price += session.get_total_sales_tickets()
                    return total_price
                else:
                    return total_price
        else:
            return total_price

    @api.multi
    def get_total_returns_tickets_z(self, today):
        session_ids = []
        total_return = 0.0
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_order_obj = []
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        total_return += session.get_total_returns_tickets_x()
                    return total_return
                else:
                    return total_return
        else:
            return total_return

    #############RECIBO WALLET CORTE Z#############
    @api.multi
    def get_wallet_reciept_z(self, today):
        session_ids = []
        orders = set()
        recran = '0-0'
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        pos_order_obj = self.env['pos.order'].search([('invoice_id','=',False),('session_id','=',session.id), ('recibo_number','!=',False),('ticket_number','=',False)], order='recibo_number asc')
                        for order in pos_order_obj:
                            orders.add(order)
                    orders = list(orders)
                    orders.sort(key=lambda o: o.recibo_number)
                    if len(orders)>1:
                        rec_in = orders[0].recibo_number
                        rec_fin = orders[-1].recibo_number
                    elif len(orders)==1:
                        rec_in = orders[0].recibo_number
                        rec_fin = '(único)'
                    else:
                        rec_in = 0
                        rec_fin = 0
                    recran = '{0}-{1}'.format(rec_in,rec_fin)
                    return recran
                return recran
        else:
            return recran

    @api.multi
    def get_total_wallet_recharges_z(self, today):
        session_ids = []
        total_price = 0.0
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_order_obj = []
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        total_price += session.get_total_wallet_recharges()
                    return total_price
                else:
                    return total_price
        else:
            return total_price

    ############################

    #############DETALLE DE PAGOS CORTE Z#############
    @api.multi
    def get_payments_z(self, today):
        session_ids = []
        orders_ids = set()
        data = {}
        total_price = 0.0
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_order_obj = []
                company_id = self.env['res.users'].browse([self._uid]).company_id.id
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        pos_order_obj = self.env['pos.order'].search([('session_id', '=', session.id),
                                                        ('state', 'in', ['paid', 'invoiced', 'done']),
                                                        ('user_id', '=', session.user_id.id), ('company_id', '=', company_id)])
                        for order in pos_order_obj:
                            orders_ids.add(order.id)
                    orders_ids = list(orders_ids)
                    if orders_ids:
                        statement_line_obj = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders_ids)])
                        if statement_line_obj:
                            a_l = []
                            for r in statement_line_obj:
                                a_l.append(r['id'])
                            self._cr.execute("select aj.name,sum(amount) from account_bank_statement_line as absl,account_bank_statement as abs,account_journal as aj " \
                                            "where absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
                                            "group by aj.name ", (tuple(a_l),))
                            data = self._cr.dictfetchall()
                            return data
                        else:
                            return data
                    else:
                        return data
                else:
                    return data
        else:
            return data

    @api.multi
    def get_payments_invoice_z(self, today):
        session_ids = []
        inv_ids =[]
        a_l = set()
        data = {}
        today = datetime.strptime(today, '%Y-%m-%d')
        today = today.date()
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        company_id = self.env['res.users'].browse([self._uid]).company_id.id
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_invoice_obj = []
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    for session in pos_session_obj:
                        start_at = session.start_at
                        stop_at = session.stop_at
                        invoice_obj = self.env["account.invoice"].search([('create_date', '>=', start_at),
                                                        ('create_date', '<=', stop_at),
                                                        ('state', '=', 'paid'),('fiscal_position_id','!=',False),
                                                        ('user_id', '=', session.user_id.id), ('company_id', '=', company_id)])
                        if invoice_obj:
                            for inv in invoice_obj:
                                inv_ids.append(inv.partner_id.id)
                            if inv_ids:
                                account_payment_obj = self.env["account.payment"].search([('partner_id', 'in', inv_ids),('payment_date', '>=', start_at),
                                                            ('payment_date', '<=', stop_at),('create_uid', '=', session.user_id.id),('company_id', '=', company_id)])
                                if account_payment_obj:
                                    for r in account_payment_obj:
                                        a_l.add(r['id'])
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue
                    a_l = list(a_l)
                    self._cr.execute("select aj.name, sum(ap.amount) from account_payment as ap, account_journal as aj " \
                                        "where ap.journal_id = aj.id  and ap.id IN %s " \
                                        "group by aj.name ", (tuple(a_l),))
                    data = self._cr.dictfetchall()
                    return data
                else:
                    return data
        else:
            return data

    ############################

    @api.model
    def get_uid(self):
        current_user_name = self.env['res.users'].browse([self._uid]).name or ' '
        return current_user_name

    @api.multi
    def get_current_date_z(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')

    @api.multi
    def get_current_time_z(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')

    @api.multi
    def get_eval_date(self, fecha):
        return datetime.strptime(fecha, '%Y-%m-%d').date()

    @api.multi
    def get_open_close_time(self, today):
        data = {}
        session_ids = []
        invran = '0-0'
        today = datetime.strptime(today,'%Y-%m-%d')
        today = today.date()
        hora = time(20,0,0)
        stop_at = datetime(today.year,today.month,today.day,23,59,59)
        start_at = datetime(today.year,today.month,today.day,0,0,1)
        if self:
            for pos in self:
                pos_config_id = pos.id
                pos_session_obj = self.env['pos.session'].search([('config_id','=',pos_config_id),('start_at','>=',start_at),('stop_at','<=',stop_at)], order="id asc")
                if pos_session_obj:
                    data["open_time"] = pos_session_obj[0].get_session_time(pos_session_obj[0].start_at)
                    data["close_time"] = pos_session_obj[-1].get_session_time(pos_session_obj[-1].stop_at)
                return data
        return data

class res_company(models.Model):
    _inherit = 'res.company'

    report_ip_address = fields.Char(string="Thermal Printer Proxy IP")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
