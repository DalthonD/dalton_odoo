odoo.define('cryo_sv.ReceiptScreenWidget', function (require) {
    'use strict';
    var screens = require('point_of_sale.screens');
    var pos_model = require('point_of_sale.models');
    var ReceiptScreenWidget = screens.ReceiptScreenWidget;
    var PaymentScreenWidget = screens.PaymentScreenWidget;
    var core = require('web.core');
    var SuperOrder = pos_model.Order.prototype;
    var QWeb = core.qweb;

	ReceiptScreenWidget.include({
		render_receipt: function() {
			this.$('.pos-receipt-container').html(QWeb.render('posticketsv', this.get_receipt_render_env()));
		},

		get_iswallet: function () {
			var order = this.pos.get_order();
			var result=false;
			var x = order.orderlines.length;
			for (var i=0;i<x;i++){
				var line = order.orderlines.models[i];
				if (line.product.display_name.includes("Wallet")){
					result=true;
				}
			}
      if (order.to_invoice === true) {
        result=true;
      }
			/*if (result==true){
				if (typeof order.recibo_number === null){
					this.pos.config.recibo_number=this.pos.config.recibo_number+1;
					order.recibo_number=this.pos.config.recibo_number
				}
			}
			else{
				if (typeof order.ticket_number === null){
					this.pos.config.ticket_number=this.pos.config.ticket_number+1;
					order.ticket_number=this.pos.config.ticket_number
				}
			}*/
			return result;
		 },
	});


	PaymentScreenWidget.include({

		validate_order: function(force_validation) {
			var order = this.pos.get_order();
			if (this.order_is_valid(force_validation)) {
				var result=false;
				var x = order.orderlines.length;
				for (var i=0;i<x;i++){
					var line = order.orderlines.models[i];
					if (line.product.display_name.includes("Wallet")){
						result=true;
					}
				}
        if (order.to_invoice === true) {
          result=true;
        }
				if (result==true){
					if (order.recibo_number === null){
						order.pos.config.recibo_number=this.pos.config.recibo_number+1;
						order.recibo_number=this.pos.config.recibo_number
					}
				}
				else{
					if (order.ticket_number === null){
						order.pos.config.ticket_number=this.pos.config.ticket_number+1;
						order.ticket_number=this.pos.config.ticket_number
					}
				}

				this.finalize_validation();
			}
		},
	});




	pos_model.Order = pos_model.Order.extend({
        init_from_JSON: function(json) {
			var self = this;
			SuperOrder.init_from_JSON.call(self,json);
			if(json.ticket_number)
				self.ticket_number = json.ticket_number;
			if(json.recibo_number)
				self.recibo_number = json.recibo_number;
		},
        initialize: function(attributes,options){
			var self = this;
			self.ticket_number = null;
			self.recibo_number = null;
			SuperOrder.initialize.call(this,attributes,options);
		},
        export_as_JSON: function() {
			var self = this;
			var loaded=SuperOrder.export_as_JSON.call(this);
			var current_order = self.pos.get_order();
			if(current_order!=null){
				loaded.ticket_number = current_order.ticket_number;
				loaded.recibo_number = current_order.recibo_number;
			}
			return loaded;
		},
    });
});;
