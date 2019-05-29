# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import fields,api,models
from datetime import datetime
from operator import itemgetter


class AllSummary(models.Model):
    _inherit = 'pos.order'

    @api.model
    def product_summary_report(self,vals):
        if(vals):
            product_summary_dict = {}
            category_summary_dict = {}
            payment_summary_dict = {}
            location_summary_dict = {}
            product_qty = 0
            location_qty = 0
            category_qty = 0
            payment = 0
            if vals.get('session_id'):
                order_detail = self.env['pos.order'].search([('session_id.id', '=', vals.get('session_id'))])
            else:
                order_detail = self.env['pos.order'].search([('date_order', '>=', vals.get('start_date')),
                                                         ('date_order', '<=', vals.get('end_date'))
                                                         ])

            if('product_summary' in vals.get('summary') or len(vals.get('summary')) == 0):
                if(order_detail):
                    for each_order in order_detail:
                        for each_order_line in each_order.lines:
                            if each_order_line.product_id.name in product_summary_dict:
                                product_qty = product_summary_dict[each_order_line.product_id.name ]
                                product_qty += each_order_line.qty
                            else:
                                product_qty = each_order_line.qty
                            product_summary_dict[each_order_line.product_id.name] = product_qty;

            if ('category_summary' in vals.get('summary') or len(vals.get('summary')) == 0):
                if (order_detail):
                    for each_order in order_detail:
                        for each_order_line in each_order.lines:
                            if each_order_line.product_id.pos_categ_id.name in category_summary_dict:
                                category_qty = category_summary_dict[each_order_line.product_id.pos_categ_id.name]
                                category_qty += each_order_line.qty
                            else:
                                category_qty = each_order_line.qty
                            category_summary_dict[each_order_line.product_id.pos_categ_id.name] = category_qty;
                    if(False in category_summary_dict):
                        category_summary_dict['Others'] = category_summary_dict.pop(False);

            if('payment_summary' in vals.get('summary') or len(vals.get('summary')) == 0):
                if (order_detail):
                    for each_order in order_detail:
                       for payment_line in each_order.statement_ids:
                            if payment_line.statement_id.journal_id.name in payment_summary_dict:
                                payment = payment_summary_dict[payment_line.statement_id.journal_id.name]
                                payment += payment_line.amount
                            else:
                                payment = payment_line.amount
                            payment_summary_dict[payment_line.statement_id.journal_id.name] = float(format(payment,'2f'));

            if ('location_summary' in vals.get('summary') or len(vals.get('summary')) == 0):
                location_list = []
                for each_order in order_detail:
                    location_summary_dict[each_order.picking_id.location_id.name] = {}
                for each_order in order_detail:
                    for each_order_line in each_order.lines:
                        if each_order_line.product_id.name in location_summary_dict[each_order.picking_id.location_id.name]:
                            location_qty = location_summary_dict[each_order.picking_id.location_id.name][
                            each_order_line.product_id.name]
                            location_qty += each_order_line.qty
                        else:
                            location_qty = each_order_line.qty
                        location_summary_dict[each_order.picking_id.location_id.name][each_order_line.product_id.name] = location_qty
                location_list.append(location_summary_dict)

        return {
                'product_summary':product_summary_dict,
                'category_summary':category_summary_dict,
                'payment_summary':payment_summary_dict,
                'location_summary':location_summary_dict,
                }

    @api.model
    def order_summary_report(self, vals):
        order_list = {}
        order_list_sorted = []
        category_list = {}
        payment_list = {}
        if vals:
            if (vals['state'] == ''):
                if vals.get('session_id'):
                    orders = self.search(
                        [('session_id.id', '=', vals.get('session_id'))])
                else:
                    orders = self.search(
                        [('date_order', '>=', vals.get('start_date')), ('date_order', '<=', vals.get('end_date'))])

                if ('order_summary_report' in vals['summary'] or len(vals['summary']) == 0):
                    for each_order in orders:
                        order_list[each_order.state] = []
                    for each_order in orders:
                        if each_order.state in order_list:
                            order_list[each_order.state].append({
                                'order_ref': each_order.name,
                                'order_date': each_order.date_order,
                                'total': float(format(each_order.amount_total, '.2f'))
                            })
                        else:
                            order_list.update({
                                each_order.state.append({
                                    'order_ref': each_order.name,
                                    'order_date': each_order.date_order,
                                    'total': float(format(each_order.amount_total, '.2f'))
                                })
                            })
                if ('category_summary_report' in vals['summary'] or len(vals['summary']) == 0):
                    count = 0.00
                    amount = 0.00
                    for each_order in orders:
                        category_list[each_order.state] = {}
                    for each_order in orders:
                        for order_line in each_order.lines:
                            if each_order.state == 'paid':
                                if order_line.product_id.pos_categ_id.name in category_list[each_order.state]:
                                    count = category_list[each_order.state][order_line.product_id.pos_categ_id.name][0]
                                    amount = category_list[each_order.state][order_line.product_id.pos_categ_id.name][1]
                                    count += order_line.qty
                                    amount += order_line.price_subtotal_incl
                                else:
                                    count = order_line.qty
                                    amount = order_line.price_subtotal_incl
                            if each_order.state == 'done':
                                if order_line.product_id.pos_categ_id.name in category_list[each_order.state]:
                                    count = category_list[each_order.state][order_line.product_id.pos_categ_id.name][0]
                                    amount = category_list[each_order.state][order_line.product_id.pos_categ_id.name][1]
                                    count += order_line.qty
                                    amount += order_line.price_subtotal_incl
                                else:
                                    count = order_line.qty
                                    amount = order_line.price_subtotal_incl
                            if each_order.state == 'invoiced':
                                if order_line.product_id.pos_categ_id.name in category_list[each_order.state]:
                                    count = category_list[each_order.state][order_line.product_id.pos_categ_id.name][0]
                                    amount = category_list[each_order.state][order_line.product_id.pos_categ_id.name][1]
                                    count += order_line.qty
                                    amount += order_line.price_subtotal_incl
                                else:
                                    count = order_line.qty
                                    amount = order_line.price_subtotal_incl
                            category_list[each_order.state].update(
                                {order_line.product_id.pos_categ_id.name: [count, amount]})
                        if (False in category_list[each_order.state]):
                            category_list[each_order.state]['others'] = category_list[each_order.state].pop(False)

                if ('payment_summary_report' in vals['summary'] or len(vals['summary']) == 0):
                    count = 0
                    for each_order in orders:
                        payment_list[each_order.state] = {}
                    for each_order in orders:
                        for payment_line in each_order.statement_ids:
                            if each_order.state == 'paid':
                                if payment_line.journal_id.name in payment_list[each_order.state]:
                                    count = payment_list[each_order.state][payment_line.journal_id.name]
                                    count += payment_line.amount
                                else:
                                    count = payment_line.amount
                            if each_order.state == 'done':
                                if payment_line.journal_id.name in payment_list[each_order.state]:
                                    count = payment_list[each_order.state][payment_line.journal_id.name]
                                    count += payment_line.amount
                                else:
                                    count = payment_line.amount
                            if each_order.state == 'invoiced':
                                if payment_line.journal_id.name in payment_list[each_order.state]:
                                    count = payment_list[each_order.state][payment_line.journal_id.name]
                                    count += payment_line.amount
                                else:
                                    count = payment_line.amount
                            payment_list[each_order.state].update(
                                {payment_line.journal_id.name: float(format(count, '.2f'))})
                return {'order_report': order_list, 'category_report': category_list, 'payment_report': payment_list,
                        'state': vals['state']}
            else:
                order_list = []
                if vals.get('session_id'):
                    orders = self.search(
                        [('session_id.id', '=', vals.get('session_id')), ('state', '=', vals.get('state'))])
                else:
                    orders = self.search(
                        [('date_order', '>=', vals.get('start_date')), ('date_order', '<=', vals.get('end_date')),
                         ('state', '=', vals.get('state'))])

                if ('order_summary_report' in vals['summary'] or len(vals['summary']) == 0):
                    for each_order in orders:
                        order_list.append({
                            'order_ref': each_order.name,
                            'order_date': each_order.date_order,
                            'total': float(format(each_order.amount_total, '.2f'))
                        })
                    order_list_sorted = sorted(order_list, key=itemgetter('order_ref'))

                if ('category_summary_report' in vals['summary'] or len(vals['summary']) == 0):
                    count = 0.00
                    amount = 0.00
                    values = []
                    for each_order in orders:
                        for order_line in each_order.lines:
                            if order_line.product_id.pos_categ_id.name in category_list:
                                count = category_list[order_line.product_id.pos_categ_id.name][0]
                                amount = category_list[order_line.product_id.pos_categ_id.name][1]
                                count += order_line.qty
                                amount += order_line.price_subtotal_incl
                            else:
                                count = order_line.qty
                                amount = order_line.price_subtotal_incl
                            category_list.update({order_line.product_id.pos_categ_id.name: [count, amount]})
                    if (False in category_list):
                        category_list['others'] = category_list.pop(False)
                if ('payment_summary_report' in vals['summary'] or len(vals['summary']) == 0):
                    count = 0
                    for each_order in orders:
                        for payment_line in each_order.statement_ids:
                            if payment_line.journal_id.name in payment_list:
                                count = payment_list[payment_line.journal_id.name]
                                count += payment_line.amount
                            else:
                                count = payment_line.amount
                            payment_list.update({payment_line.journal_id.name: float(format(count, '.2f'))})
            return {'order_report': order_list_sorted, 'category_report': category_list, 'payment_report': payment_list,
                    'state': vals['state']}

    @api.model
    def payment_summary_report(self, vals):
        if (vals):
            journals_detail = {}
            salesmen_detail = {}
            summary_data = {}
            if vals.get('session_id'):
                order_detail = self.env['pos.order'].search([('session_id.id', '=', vals.get('session_id'))])
            else:
                order_detail = self.env['pos.order'].search([('date_order', '>=', vals.get('start_date')),
                                                         ('date_order', '<=', vals.get('end_date'))
                                                         ])
            if 'journals' in vals.get('summary'):
                if (order_detail):
                    for each_order in order_detail:
                        order_date = each_order.date_order
                        date1 = order_date
                        month_year = date1.strftime("%B-%Y")
                        if not month_year in journals_detail:
                            journals_detail[month_year] = {}
                            for payment_line in each_order.statement_ids:
                                if payment_line.statement_id.journal_id.name in journals_detail[month_year]:
                                    payment = journals_detail[month_year][payment_line.statement_id.journal_id.name]
                                    payment += payment_line.amount
                                else:
                                    payment = payment_line.amount
                                journals_detail[month_year][payment_line.statement_id.journal_id.name] = float(
                                    format(payment, '2f'));
                        else:
                            for payment_line in each_order.statement_ids:
                                if payment_line.statement_id.journal_id.name in journals_detail[month_year]:
                                    payment = journals_detail[month_year][payment_line.statement_id.journal_id.name]
                                    payment += payment_line.amount
                                else:
                                    payment = payment_line.amount
                                journals_detail[month_year][payment_line.statement_id.journal_id.name] = float(
                                    format(payment, '2f'));
                    for journal in journals_detail.values():
                        for i in journal:
                            if i in summary_data:
                                total = journal[i] + summary_data[i]
                            else:
                                total = journal[i]
                            summary_data[i] = float(format(total, '2f'));

            if 'sales_person' in vals.get('summary'):
                if (order_detail):
                    for each_order in order_detail:
                        order_date = each_order.date_order
                        date1 = order_date
                        month_year = date1.strftime("%B-%Y")
                        if each_order.user_id.name not in salesmen_detail:
                            salesmen_detail[each_order.user_id.name] = {}
                            if not month_year in salesmen_detail[each_order.user_id.name]:
                                salesmen_detail[each_order.user_id.name][month_year] = {}
                                for payment_line in each_order.statement_ids:
                                    if payment_line.statement_id.journal_id.name in \
                                            salesmen_detail[each_order.user_id.name][month_year]:
                                        payment = salesmen_detail[each_order.user_id.name][month_year][
                                            payment_line.statement_id.journal_id.name]
                                        payment += payment_line.amount
                                    else:
                                        payment = payment_line.amount
                                    salesmen_detail[each_order.user_id.name][month_year][
                                        payment_line.statement_id.journal_id.name] = float(
                                        format(payment, '2f'));
                        else:
                            if not month_year in salesmen_detail[each_order.user_id.name]:
                                salesmen_detail[each_order.user_id.name][month_year] = {}
                                for payment_line in each_order.statement_ids:
                                    if payment_line.statement_id.journal_id.name in \
                                            salesmen_detail[each_order.user_id.name][month_year]:
                                        payment = salesmen_detail[each_order.user_id.name][month_year][
                                            payment_line.statement_id.journal_id.name]
                                        payment += payment_line.amount
                                    else:
                                        payment = payment_line.amount
                                    salesmen_detail[each_order.user_id.name][month_year][
                                        payment_line.statement_id.journal_id.name] = float(
                                        format(payment, '2f'));
                            else:
                                for payment_line in each_order.statement_ids:
                                    if payment_line.statement_id.journal_id.name in \
                                            salesmen_detail[each_order.user_id.name][month_year]:
                                        payment = salesmen_detail[each_order.user_id.name][month_year][
                                            payment_line.statement_id.journal_id.name]
                                        payment += payment_line.amount
                                    else:
                                        payment = payment_line.amount
                                    salesmen_detail[each_order.user_id.name][month_year][
                                        payment_line.statement_id.journal_id.name] = float(
                                        format(payment, '2f'));
        return {
            'journal_details': journals_detail,
            'salesmen_details': salesmen_detail,
            'summary_data': summary_data
        }

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
