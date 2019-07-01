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
            where s.sv_declaracion=cast({0} as varchar) order by f.date_invoice desc;""".format(self.sv_declaracion)
            self._cr.execute(invoices)
            if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
                data = self._cr.dictfetchall()
            return data
        else:
            return data

    def get_product_details(self):
        data = {}
        if self:
            adjustment = """Select R.codigo as codigo
            ,R.descripcion as descripcion
            ,R.aduana_des as aduana_des
            ,R.posicion as posicion
            ,R.cantidad as cantidad
            ,R.precio_unit as precio_unit
            ,R.fob as fob
            ,R.seguro as seguro
            ,R.flete as flete
            /*Calculando CIF*/
            ,sum(R.fob+R.seguro+R.flete) as cif
            ,R.impuesto as impuesto
            ,R.otros as otros
            /*Calculando Costo Total*/
            ,sum(R.fob+R.seguro+R.flete+R.impuesto+R.otros) as costo_total
            /*Calculando Costo Unitario*/
            ,(sum(R.fob+R.seguro+R.flete+R.impuesto+R.otros)/R.cantidad) as costo_unitario
            from (
            select DISTINCT coalesce(coalesce(pp.default_code,pt.default_code),cast(10000+pp.id as VARCHAR)) as codigo
            ,coalesce(coalesce(pt.description_purchase,pt.description),pt.name) as descripcion
            ,(select name from purchase_order_line pol where pol.product_id=pp.id group by name) as aduana_des
            ,null as posicion
            ,cast(sval.quantity as integer) as cantidad
            ,sval.former_cost_per_unit as precio_unit
            ,sval.former_cost as fob

            ,/*Calculando Seguros*/
            coalesce((select sum(sval1.additional_landed_cost)
            from stock_valuation_adjustment_lines sval1
            inner join stock_landed_cost_lines slcl1 on slcl1.id=sval1.cost_line_id
            inner join product_product pp1 on pp1.id=slcl1.product_id
            inner join product_template pt1 on pt1.id=pp1.product_tmpl_id
            inner join stock_landed_cost slc1 on slc1.id=sval1.cost_id
            where slc1.sv_declaracion=cast({0} as VARCHAR)
            and sval1.product_id=pp.id
            and pt1.landed_cost_ok=true
            and pt1.sv_tipo_costo='Seguro'), 0.00) as seguro

            ,/*Calculando Flete*/
            coalesce((select sum(sval2.additional_landed_cost)
            from stock_valuation_adjustment_lines sval2
            inner join stock_landed_cost_lines slcl2 on slcl2.id=sval2.cost_line_id
            inner join product_product pp2 on pp2.id=slcl2.product_id
            inner join product_template pt2 on pt2.id=pp2.product_tmpl_id
            inner join stock_landed_cost slc2 on slc2.id=sval2.cost_id
            where slc2.sv_declaracion=cast({0} as VARCHAR)
            and sval2.product_id=pp.id
            and pt2.landed_cost_ok=true
            and pt2.sv_tipo_costo='Flete'), 0.00) as flete

            ,/*Calculando Impuestos*/
            coalesce((select sum(sval3.additional_landed_cost)
            from stock_valuation_adjustment_lines sval3
            inner join stock_landed_cost_lines slcl3 on slcl3.id=sval3.cost_line_id
            inner join product_product pp3 on pp3.id=slcl3.product_id
            inner join product_template pt3 on pt3.id=pp3.product_tmpl_id
            inner join stock_landed_cost slc3 on slc3.id=sval3.cost_id
            where slc3.sv_declaracion=cast({0} as VARCHAR)
            and sval3.product_id=pp.id
            and pt3.landed_cost_ok=true
            and pt3.sv_tipo_costo='Impuestos'), 0.00) as impuesto

            ,/*Calculando Otros*/
            coalesce((select sum(sval4.additional_landed_cost)
            from stock_valuation_adjustment_lines sval4
            inner join stock_landed_cost_lines slcl4 on slcl4.id=sval4.cost_line_id
            inner join product_product pp4 on pp4.id=slcl4.product_id
            inner join product_template pt4 on pt4.id=pp4.product_tmpl_id
            inner join stock_landed_cost slc4 on slc4.id=sval4.cost_id
            where slc4.sv_declaracion=cast({0} as VARCHAR)
            and sval4.product_id=pp.id
            and pt4.landed_cost_ok=true
            and pt4.sv_tipo_costo='Otros'), 0.00) as otros


            from stock_valuation_adjustment_lines sval
            inner join product_product pp on pp.id=sval.product_id
            inner join product_template pt on pt.id=pp.product_tmpl_id
            inner join stock_landed_cost_lines slcl on slcl.id=sval.cost_line_id
            inner join stock_landed_cost slc on slc.id=sval.cost_id
            /*Condiciones*/
            where slc.sv_declaracion=cast({0} as VARCHAR)
            /*Agrupaciones*/
            group by codigo,
            descripcion,
            aduana_des,
            cantidad,
            precio_unit, fob, slcl.id, sval.cost_line_id,pp.id,pt.id,seguro,flete
            order by codigo asc) R group by
            codigo,
            descripcion,
            aduana_des,
            posicion,
            cantidad,
            precio_unit,
            fob,
            seguro,
            flete,
            impuesto,
            otros
            /*Orden*/
            order by R.codigo""".format(self.sv_declaracion)
            self._cr.execute(adjustment)
            if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
                data = self._cr.dictfetchall()
            return data
        return data
