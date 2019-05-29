# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools 
from odoo.osv import expression
from odoo.exceptions import ValidationError


class sv_product_fiscal_type(models.Model):
	_name= 'strategiksv.product_fiscal_type'
	name= fields.Char("Categoria fiscal del producto")
	comment = fields.Text('Descripcion de la categoria de productos')
	company_id=fields.Many2one('res.company',string='Company',help='Company',default=lambda self: self.env.user.company_id.id)


class sv_company_tax(models.Model):
	_name='strategiksv.company_tax'
	name= fields.Char("Impuestos nombre de la clasificacion")
	fiscal_position_id=fields.Many2one('account.fiscal.position',string='Posicion fiscal',help='Posicion fiscal a asociar')
	product_fiscal_type_id=fields.Many2one('strategiksv.product_fiscal_type',string='Tipo de producto fiscal',help='Posicion fiscal a asociar')
	sale_tax_ids=fields.Many2many('account.tax',relation='strategiksv_company_sale_tax',string='Impuestos a aplicar durante la venta')
	buy_tax_ids=fields.Many2many('account.tax',relation='strategiksv_company_buy_tax',string='Impuestos a aplicar durante la compra')
	company_id=fields.Many2one('res.company',string='Company',help='Company',default=lambda self: self.env.user.company_id.id)
	


class sv_company(models.Model):
	_inherit = 'res.company'
	sv_account_sing_ids=fields.One2many('strategiksv.accountsign','company_id','Signos de las cuentas')
	sv_account_ingreso= fields.Char("condicion de las cuentas de Ingresos")
	sv_account_egreso= fields.Char("condicion de las cuentas de Egresos")
	sv_account_activo= fields.Char("condicion de las cuentas de Activo")
	sv_account_pasivo= fields.Char("condicion de las cuentas de Pasivo")
	sv_account_capital= fields.Char("condicion de las cuentas de Capital")
	sv_account_cierre= fields.Char("condicion de las cuentas de Cierre")
	sv_account_efectivo= fields.Char("condicion de las cuentas de efectivo y equivalente")
	sv_efectivo_depth= fields.Integer("Profundida del flujo de efectivo")
	
	
	sv_elebora_partida= fields.Char("Elabora")
	sv_revisa_partida= fields.Char("Revisa")
	sv_aprueba_partida= fields.Char("Aprueba")
	sv_nit= fields.Char("NIT")
	sv_nrc= fields.Char("NRC")
	sv_invoice_serie_size = fields.Integer("Longitud de la serie de la factura")
	sv_company_tax_ids=fields.One2many('strategiksv.company_tax','company_id','Tabla de impuesto')
	sv_iva_compra=fields.Many2one('account.tax',string='IVA Compra',help='IVA Compra')
	sv_iva_venta_consumidor=fields.Many2one('account.tax',string='IVA venta consumidor',help='IVA venta')
	sv_iva_venta_contribuyente=fields.Many2one('account.tax',string='IVA venta contribuyente',help='IVA venta contribuyente')
	sv_retencion=fields.Many2one('account.tax',string='Retension',help='Retension')
	sv_perseccion=fields.Many2one('account.tax',string='Perseccion',help='Perseccion')
	sv_formato_factura=fields.Char("Formato factura")
	sv_formato_creditofiscal=fields.Char("Formato credito fiscal")
	sv_cuenta_salarios=fields.Char("Codigo de la cuenta de provision de salarios")
	
	


class sv_account_fiscal_position(models.Model):
	_inherit = 'account.fiscal.position'
	sv_contribuyente = fields.Boolean('Es contribuyente')
	sv_persona=fields.Selection([('Natural','Natural'), ('Juridica','Juridica')],default='Natural',string='Tipo de persona')
	sv_tamanio=fields.Selection([('PYME','PYME'), ('Grande','Grande'), ('Excluido','Excluido')],default='PYME',string='Tipo NIF')
	sv_clase=fields.Selection([('Gravado','Gravado'), ('Exento','Exento'), ('No Aplica','No Aplica')],default='Gravado',string='Clase de Impuesto')
	sv_region=fields.Selection([('Local','Local'), ('No Domiciliado','No Domiciliado'), ('Paraiso Fiscal','Paraiso Fiscal')],default='Local',string='Tipo de Region')
	name = fields.Char('Posicion Fiscal',compute='_end_attributes',store=True,required=False)
	sv_company_tax_ids=fields.One2many('strategiksv.company_tax','fiscal_position_id','Tabla de impuesto')
	
	@api.one
	@api.depends('sv_contribuyente', 'sv_persona', 'sv_tamanio', 'sv_clase', 'sv_region')
	def _end_attributes(self):
		if self.sv_contribuyente == True:
			self.name = 'Contribuyente'
		else:
			self.name = 'No Contribuyente'
		self.name= self.name + ', '+self.sv_persona+ ', '+self.sv_tamanio+', '+self.sv_clase+', '+self.sv_region; 
		self.sv_name = self.name


class sv_invoice_line(models.Model):
	_inherit = 'account.invoice.line'
	sv_iva=fields.Float("Impuesto del IVA")
	sv_total_con_iva=fields.Float("Precio con IVA")
	sv_iva_unitario=fields.Float("Precio unitario con IVA")
	
	def _set_taxes(self):
		self.sv_iva = 0
		taxes=None
		fp_taxes=None
		for companytax in self.invoice_id.company_id.sv_company_tax_ids:
			if (companytax.fiscal_position_id.id == self.invoice_id.fiscal_position_id.id):
				if (self.product_id):
					if (self.product_id.product_fiscal_type_id.id == companytax.product_fiscal_type_id.id):
						if self.invoice_id.type in ('in_invoice', 'in_refund'):
							self.invoice_line_tax_ids = taxes = fp_taxes = companytax.buy_tax_ids
						else:
							self.invoice_line_tax_ids = taxes = fp_taxes = companytax.sale_tax_ids
					else:
						self.sv_iva = 0
				else:
					self.sv_iva = 0
			else:
				self.sv_iva = 0
		fix_price = self.env['account.tax']._fix_tax_included_price
		if taxes is not None:
			if self.invoice_id.type in ('in_invoice', 'in_refund'):
				prec = self.env['decimal.precision'].precision_get('Product Price')
				if not self.price_unit or float_compare(self.price_unit, self.product_id.standard_price, precision_digits=prec) == 0:
					self.price_unit = fix_price(self.product_id.standard_price, taxes, fp_taxes)
			else:
				self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)


class account_invoice(models.Model):
	_inherit = 'account.invoice'
	sv_credito_fiscal=fields.Boolean("Credito Fiscal",default=True)
	sv_fecha_tax=fields.Date("Fecha para impuestos")
	sv_importacion_number=fields.Char("Referencia de Importacion")
	sv_no_tax=fields.Boolean("Fuera del ambito fiscal")
	sv_region=fields.Selection([('Local','Local'), ('No Domiciliado','No Domiciliado'), ('Paraiso Fiscal','Paraiso Fiscal')],string='Tipo de Region',related='fiscal_position_id.sv_region',store=True)
	sv_reporte = fields.Char('reporte',compute='_select_report',store=True,required=False)
	
	@api.one
	@api.depends('company_id', 'fiscal_position_id','partner_id')
	def _select_report(self):
		if self.fiscal_position_id.sv_contribuyente == True:
			self.sv_reporte = self.company_id.sv_formato_creditofiscal
		else:
			self.sv_reporte = self.company_id.sv_formato_factura
	
	@api.model
	def create(self, vals):
		
		#se calcula el impuesto si es iva se asume el de la empresa
		for inv in self:
			for record in inv.invoice_line_ids:
				record.sv_iva=0
				record.sv_iva_unitario=0
				if (record.product_id):
					record.sv_iva=0
					record.sv_iva_unitario=0
				else:
					raise ValidationError("Debe especificarse un producto")
				if record.invoice_line_tax_ids is not None:
					for tax in record.invoice_line_tax_ids:
						if tax.tax_group_id.name=='iva':
							record.sv_iva=record.sv_iva+((record.price_subtotal_signed*tax.amount)/100.00)
							record.sv_iva_unitario=record.sv_iva_unitario+((record.price_unit*tax.amount)/100.00)
					record.sv_total_con_iva=record.price_subtotal_signed+record.sv_iva
		res = super(account_invoice, self).create(vals)
		return res

	@api.multi
	def write(self, vals):
		#se calcula el impuesto si es iva se asume el de la empresa
		res = super(account_invoice, self).write(vals)
		#se calcula el impuesto si es iva se asume el de la empresa
		for inv in self:
			for record in inv.invoice_line_ids:
				record.sv_iva=0
				record.sv_iva_unitario=0
				if (record.product_id):
					record.sv_iva=0
					record.sv_iva_unitario=0
				else:
					raise ValidationError("Debe especificarse un producto")
				if record.invoice_line_tax_ids is not None:
					for tax in record.invoice_line_tax_ids:
						if tax.tax_group_id.name=='iva':
							record.sv_iva=record.sv_iva+((record.price_subtotal_signed*tax.amount)/100.00)
							record.sv_iva_unitario=record.sv_iva_unitario+((record.price_unit*tax.amount)/100.00)
					record.sv_total_con_iva=record.price_subtotal_signed+record.sv_iva
		return res



class sv_account_journal(models.Model):
	_inherit = 'account.journal'
	sv_caja_chica = fields.Boolean("Caja chica")
	sv_formato_cheque=fields.Char("Formato cheque")

class sv_caja_chica(models.Model):
	
	@api.one
	@api.depends('line_ids', 'sv_monto_inicial')
	def _end_balance(self):
		self.sv_total = sum([line.amount for line in self.line_ids])
		self.sv_saldo = self.sv_monto_inicial - self.sv_total

	_name = 'strategiksv.cajachica'
	name = fields.Char("Caja chica")
	journal_id = fields.Many2one('account.journal',string='Libro asociado',help='Libro asociado')
	account_id = fields.Many2one(related='journal_id.default_credit_account_id', string="cuenta a utilizar")
	user_id = fields.Many2one('res.users',string='Responsable',help='Responsable')
	partner_id = fields.Many2one('res.partner',string='Proveedor asociado',help='Proveedor asociado')
	sv_monto_inicial = fields.Float("Monto inicial")
	line_ids = fields.One2many('account.payment','sv_cajachica_id','Pagos realizados')
	sv_total = fields.Float('Total de pagos',compute='_end_balance',store=True)
	sv_saldo = fields.Float("Saldo de la caja",compute='_end_balance',store=True)
	sv_fecha_apertura = fields.Date("Fecha de apertura")
	sv_fecha_cierre = fields.Date("Fecha de cierre")
	state = fields.Selection([('draft','Borrador'), ('open','Abierto'),('closed','Cerrado')],default='draft')
	
	@api.multi
	def open_cc(self):
		for cc in self:
			cc.state='open'
#			cc.sv_fecha_apertura=fields.Date.today
	
	@api.multi
	def close_cc(self):
		for cc in self:
			cc.state='closed'
#			cc.sv_fecha_cierre=fields.Date.today


class sv_payment(models.Model):
	_inherit ='account.payment'
	sv_caja_chica = fields.Boolean(related='journal_id.sv_caja_chica', store=True, string="Caja chica")
	sv_cajachica_id= fields.Many2one('strategiksv.cajachica',string='Caja chica asociada',help='Caja chica asociada')
	sv_reporte = fields.Char(related='journal_id.sv_formato_cheque', store=True, string="formato")
	sv_referencia = fields.Char("Numero cheque/transferencia")
	sv_resumen= fields.Char("Concepto del pago")
	state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
	
	@api.multi
	def cancel_payment(self):
		for cc in self:
			if cc.state == 'draft':
				cc.state='cancelled'
			else:
				raise ValidationError("El pago debe estar en modo borrador")
	
	
	@api.one
	@api.constrains('sv_caja_chica', 'sv_cajachica_id')
	def _check_description(self):
		if self.sv_caja_chica == True:
			if self.sv_cajachica_id == False:
				raise ValidationError("Debe seleccionarse una caja chica")
class sv_account_partida(models.Model):
	_name= 'strategiksv.partida'
	name= fields.Char("Nombre de la partida")
	sv_number=fields.Char("Numero de la partida")
	state = fields.Selection([('draft','Borrador'), ('closed','Cerrado')],default='draft')
	sv_concepto = fields.Text("Concepto")
	journal_id = fields.Many2one('account.journal',string='Diario',help='Diario')


class sv_account_move(models.Model):
	_inherit = 'account.move'
	sv_concepto= fields.Text("Concepto")
	sv_elebora= fields.Char("Elabora",default=lambda self: self.env.user.company_id.sv_elebora_partida)
	sv_revisa= fields.Char("Revisa",default=lambda self: self.env.user.company_id.sv_revisa_partida)
	sv_aprueba= fields.Char("Aprueba",default=lambda self: self.env.user.company_id.sv_aprueba_partida)
	sv_noagrupar= fields.Boolean("No agrupar")
	partida_id= fields.Many2one('strategiksv.partida',string='Partida',help='Partida')
	
	@api.multi
	def post(self,invoice=False):
		inv=invoice
		res = super(sv_account_move,self).post(inv)
		if self.sv_noagrupar:
			self.env['job.container'].create({'sv_concepto': self.sv_concepto,'journal_id':self.journal_id,'state':'draft'})


class sv_account_move_line(models.Model):
	_inherit = 'account.move.line'
	sv_concepto= fields.Text("Concepto")
	
	@api.one
	@api.constrains('account_id')
	def _check_account(self):
		if self.account_id.internal_type == 'view':
			raise ValidationError("Debe seleccionar una cuenta que no sea de mayor")
	
class sv_account_sign(models.Model):
	_name= 'strategiksv.accountsign'
	name= fields.Char("Codigo que aplica el signo negativo")
	negativo = fields.Boolean('El Signo es negativo') 
	company_id=fields.Many2one('res.company',string='Company',help='Company')


class sv_landed_cost(models.Model):
	_inherit = 'stock.landed.cost'
	sv_referencia=fields.Char("Referencia")
	sv_declaracion=fields.Char("Declaracion No.")
	sv_guia=fields.Char("Guia/BL")
	sv_comentario=fields.Char("Descripcion")
	
class sv_product_category(models.Model):
	_inherit = 'product.category'
	company_id=fields.Many2one('res.company',string='Company',help='Company')
	

class sv_product_tax(models.Model):
	_inherit = 'product.template'
	product_fiscal_type_id=fields.Many2one('strategiksv.product_fiscal_type',string='Tipo de producto fiscal',help='Posicion fiscal a asociar')
	sv_tipo_costo=fields.Selection([('Seguro','Seguro'), ('Flete','Flete'), ('Impuestos','Impuestos'), ('Otros','Otros')],default='Otros',string='Tipo de Costo')

class sv_landed_cost(models.Model):
	_inherit = 'stock.landed.cost'
	sv_referencia=fields.Char("Referencia")
	sv_declaracion=fields.Char("Declaracion No.")
	sv_guia=fields.Char("Guia/BL")
	sv_comentario=fields.Char("Descripcion")
	
