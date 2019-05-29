# -*- coding: utf-8 -*-
from odoo import http

# class Strategiksv(http.Controller):
#     @http.route('/strategiksv/strategiksv/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/strategiksv/strategiksv/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('strategiksv.listing', {
#             'root': '/strategiksv/strategiksv',
#             'objects': http.request.env['strategiksv.strategiksv'].search([]),
#         })

#     @http.route('/strategiksv/strategiksv/objects/<model("strategiksv.strategiksv"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('strategiksv.object', {
#             'object': obj
#         })