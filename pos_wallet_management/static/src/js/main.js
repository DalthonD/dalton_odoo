/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_wallet_management.pos_wallet_management', function(require){
"use strict";
    var screens = require('point_of_sale.screens');
    var pos_model = require('point_of_sale.models');
    var rpc = require('web.rpc')
    var PosDB = require('point_of_sale.DB');
    var core = require('web.core');
    var popup_widget = require('point_of_sale.popups');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var gui = require('point_of_sale.gui');
    var chrome = require('point_of_sale.chrome');
    var _t = core._t;
    var utils = require('web.utils');
    var round_di = utils.round_decimals;
    var SuperPaymentline = pos_model.Paymentline.prototype;
    var SuperOrder = pos_model.Order.prototype;
    var model_list = pos_model.PosModel.prototype.models;

    var journal_model = null;
    pos_model.load_fields('account.journal','wallet_journal');
    pos_model.load_fields('res.partner',['wallet_credits','wallet_id']);

    //--Fetching model dictionary--
    for(var i = 0,len = model_list.length;i<len;i++){
        if(model_list[i].model == "account.journal"){
            journal_model = model_list[i];
            break;
        }
    }

    //--Searching wallet journal--
    var super_journal_loaded = journal_model.loaded;
    journal_model.loaded = function(self, journals){
        super_journal_loaded.call(this,self,journals);
        journals.forEach(function(journal){
            if(journal.wallet_journal){
                self.db.wallet_journal = journal;
                return true;
            }
        });
    };

    // --set wallet product----
    PosDB.include({
	    add_products: function(products){
            var self = this;
           for(var i = 0, len = products.length; i < len; i++){
                if(products[i].default_code == 'wk_wallet'){
                    products[i].not_returnable = true;
                    self.wallet_product = products[i];
                }
           }
            self._super(products)
        }
    });

// ---load wallet model---------------------
    pos_model.load_models([{
		model: 'pos.wallet',
		fields: ['name','partner_id','amount'],
		domain: function(self){
			return [['state','=','confirm']]
		},
		loaded: function(self,wallets){

            wallets = wallets.sort(function(a,b){
                return b.id - a.id;
            });
            self.db.all_wallets = wallets;
            self.db.wallet_by_name = {};
            wallets.forEach(function(wallet){
                self.db.wallet_by_name[wallet.name] = wallet;
            })
		}
	}])

    pos_model.Order = pos_model.Order.extend({
        init_from_JSON: function(json) {
			var self = this;
			SuperOrder.init_from_JSON.call(self,json);
			if(json.wallet_recharge_data)
				self.wallet_recharge_data = json.wallet_recharge_data;
		},
        initialize: function(attributes,options){
			var self = this;
			self.wallet_recharge_data = null;
			SuperOrder.initialize.call(this,attributes,options);
		},
        export_as_JSON: function() {
			var self = this;
			var loaded=SuperOrder.export_as_JSON.call(this);
			var current_order = self.pos.get_order();
			if(current_order!=null)
			{
				loaded.wallet_recharge_data = current_order.wallet_recharge_data;
			}
			return loaded;
		},
        remove_paymentline: function(line){
            var self = this;
            if(line && line.is_wallet_payment_line){
                $('#use_wallet_payment').prop('checked', false);
                if(self.pos.get_order().get_client())
                    $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + self.pos.chrome.format_currency(self.pos.get_order().get_client().wallet_credits) + "</span>");
            }
            SuperOrder.remove_paymentline.call(this, line);
        },
        set_client: function(client){
            var self = this;
            SuperOrder.set_client.call(self,client);
            if (self.pos.get_order() &&  self.pos.chrome.screens.payment && self.pos.chrome.screens.payment.check_existing_wallet_line())
                self.pos.get_order().remove_paymentline(self.pos.chrome.screens.payment.check_existing_wallet_line());
        },
        add_product: function(product, options){
            var self = this;
            if(self.pos.db.wallet_product && product.id == self.pos.db.wallet_product.id && !self.pos.get_order().wallet_recharge_data){
                self.pos.gui.show_popup("wallet_recharge_by_number");
            }
            else
                SuperOrder.add_product.call(self,product,options);
        }
    });

    pos_model.Paymentline = pos_model.Paymentline.extend({
        initialize: function(attributes, options){
            this.is_wallet_payment_line = false;
            SuperPaymentline.initialize.call(this, attributes, options);
        },
    });

    var WkErrorNotifyPopopWidget = popup_widget.extend({
		template: 'WkErrorNotifyPopopWidget',
		events:{
			'click .button.cancel': 'click_cancel'
		},
		show: function(options){
			var self = this;
			self._super(options);
			this.options = options;
			setTimeout(function(){
				$('.move').addClass('complete');
			},500)

		}
	});
	gui.define_popup({
		name: 'wk_error_notify',
		widget: WkErrorNotifyPopopWidget
	});

    var CreateWalletPopopWidget = popup_widget.extend({
		template: 'CreateWalletPopopWidget',
		events:{
			'click .cancel_recharge': 'click_cancel',
            'click .create_wallet':'click_create_wallet'
		},
		show: function(options){
			var self = this;
			self._super(options);
			this.options = options;
			setTimeout(function(){
				$('.move').addClass('complete');
			},500)
            self.$('.create_wallet').css({'pointer-events':'all'});
		},
        click_create_wallet:function(){
           var self = this;
           if(self.options && self.options.partner){
                var partner = self.options.partner;
                self.$('.button.create_wallet').css({'pointer-events':'none'})
                rpc.query({
					model:'pos.wallet',
					method:'create_wallet_by_rpc',
					args:[{'partner_id':parseInt(partner.id)}]
				})
                .done(function(result){
                    partner.wallet_id = [result.id,result.name];
                    var wallet_details = result;
                    wallet_details['partner_id']=[partner.id,partner.name];
                    wallet_details['partner']= self.options.partner;
                    if($('.client-line.highlight .wallet_credits').length)
                        $('.client-line.highlight .wallet_credits').text(self.format_currency(0));
                    else{
                        let client_line = $($('.client-line')[$('.client-line').length-1]);
                        let data_id = client_line.data('id');
                        let partner = self.pos.db.get_partner_by_id(data_id);
                        client_line.ch
                        if (partner && partner.wallet_id){
                            client_line.click();
                            client_line.children('.wallet_credits').text(self.format_currency(partner.wallet_credits));
                        }
                    }

                    self.pos.db.wallet_by_name[result.name] = wallet_details;
                    self.pos.db.all_wallets.push(wallet_details);
                    self.$('.wk_confirm_mark').hide();
                    self.$('.wallet_status').css({'display': 'inline-block'});
                    self.$('#order_sent_status').hide();
                    self.$('.wallet_status').removeClass('order_done');
                    self.$('.show_tick').hide();
                    setTimeout(function(){
                        $('.wallet_status').addClass('order_done');
                        $('.show_tick').show();
                        $('#order_sent_status').show();
                        $('.wallet_status').css({'border-color':'#5cb85c'});
                        self.$('.wk-alert center h2').text("Wallet Created !!!!!");

                    },500)
                    setTimeout(function(){
                         self.pos.gui.show_popup('wallet_recharge',{'partner':partner});
                    },1000);
                    $('.recharge_wallet').show();
                    $('.create_wallet').hide();
                })
                .fail(function(unused, event) {
                    self.gui.show_popup('wk_error_notify', {
                        title: _t('Failed To create wallet'),
                        body: _t('Please make sure you are connected to the network.'),
                    });
                })
           }
        }
	});
	gui.define_popup({
		name: 'create_wallet',
		widget: CreateWalletPopopWidget
	});

    var WkWalletRechargePopup = popup_widget.extend({
		template: 'WkWalletRechargePopup',
		events:{
			'click .cancel_recharge': 'wk_click_cancel',
            'click .button.validate_recharge': 'wk_validate_recharge',
            'focusout .rechage_amount':'focusout_wallet_recharge',
            'focus .rechage_amount':'focus_wallet_recharge',
            'focusout .recharge_reason':'focusout_wallet_recharge',
            'focus .recharge_reason':'focus_wallet_recharge',
        },
        focus_wallet_recharge: function(){
            var self = this;
			if(self.gui && self.gui.get_current_screen() == 'payment'){
				var paymentscreen = self.pos.gui.chrome.screens.payment
				$('body').off('keypress', paymentscreen.keyboard_handler);
                $('body').off('keydown', paymentscreen.keyboard_keydown_handler);
                window.document.body.removeEventListener('keypress',paymentscreen.keyboard_handler);
                window.document.body.removeEventListener('keydown',paymentscreen.keyboard_keydown_handler);
			}
        },

        focusout_wallet_recharge:function(){
            var self = this;
            if(self.gui && self.gui.get_current_screen() == 'payment'){
                var paymentscreen = self.pos.gui.chrome.screens.payment;
                $('body').keypress(paymentscreen.keyboard_handler);
                $('body').keydown(paymentscreen.keyboard_keydown_handler);
                window.document.body.addEventListener('keypress',paymentscreen.keyboard_handler);
                window.document.body.addEventListener('keydown',paymentscreen.keyboard_keydown_handler);
            }
        },
		show: function(options){
			var self = this;
			self._super(options);
			self.options = options;
			setTimeout(function(){
				$('.move').addClass('complete');
			},500)
            self.$('.rechage_amount').focus();

		},
        wk_click_cancel: function(){
            var self = this;
            this.pos.gui.close_popup();
        },

        wk_validate_recharge: function(){
            var self = this;
            if(self.options && self.options.partner){
                var recharge_amount = parseFloat(self.$('.rechage_amount').val());
                var reason = self.$('.recharge_reason').val();
                if(recharge_amount<=0 || !recharge_amount){
                    self.$('.rechage_amount').removeClass('text_shake');
                    self.$('.rechage_amount').focus();
                    self.$('.rechage_amount').addClass('text_shake');
					return;

                }
                else if(reason == ""){
                    self.$('.recharge_reason').removeClass('text_shake');
                    self.$('.recharge_reason').focus();
                    self.$('.recharge_reason').addClass('text_shake');
					return;
                }
                else{
                    var wallet_product = self.pos.db.wallet_product;
                    if(wallet_product){
                        var trans_data = {};
                        trans_data.amount = recharge_amount;
                        trans_data.trans_reason = reason;
                        trans_data.created_by = parseInt(self.pos.cashier ? self.pos.cashier.id : self.pos.user.id);
                        trans_data.partner_id = parseInt(self.options.partner.id);
                        trans_data.wallet_id = parseInt(self.options.partner.wallet_id[0]);
                        trans_data.payment_type = 'CREDIT';
                        trans_data.wallet_product_id = wallet_product.id;
                        trans_data.state = 'confirm'
                        self.chrome.widget.order_selector.neworder_click_handler();
                        var curren_order = self.pos.get_order();
                        curren_order.wallet_recharge_data = trans_data;
                        curren_order.add_product(wallet_product, {quantity: 1, price: recharge_amount });
                        curren_order.set_client(self.options.partner);
                        self.pos.gui.show_screen('payment');
                        curren_order.save_to_db();
                    }
                    else{
                        self.pos.gui.show_popup('wk_error_notify', {
							title: _t('Failed To Recharge Wallet.'),
							body: _t('No wallet product is available in POS.'),
						});
                    }

                }
            }

        },
	});
    gui.define_popup({
		name: 'wallet_recharge',
		widget: WkWalletRechargePopup
	});

     var MainWalletRechargePopup = popup_widget.extend({
		template: 'MainWalletRechargePopup',
		events:{
			'click .cancel_recharge': 'wk_click_cancel',
			'click .button.validate_recharge': 'wk_validate_recharge',
            'keyup .wallet_input': 'wallet_key_press_input',
            'focusout .wallet_input':'focusout_wallet_input',
            'focus .wallet_input':'focus_wallet_input',
            'click .button.validate_wallet':'click_validate_wallet',
		},

		show: function(options){
			var self = this;
			self._super(options);
			this.options = options;
			setTimeout(function(){
				$('.move').addClass('complete');
			},500);
            $('.wallet_input').focus();
            self.index = -1;
			self.parent = this.$('.wallet-holder');
		},

        wallet_key_press_input: function(event){
            var self = this;
			var updown_press;
			var all_wallets = self.pos.db.all_wallets;
			$('.wallet-holder ul').empty();
			var search = self.$('.wallet_input').val();
			self.$('.wallet-holder').show();
			search = new RegExp(search.replace(/[^0-9a-z_]/i), 'i');
			for(var index in all_wallets){
				if(all_wallets[index].name.match(search)){
			   	    $('.wallet-holder ul').append($("<li><span class='wallet-name'>" + all_wallets[index].name + "</span></li>"));
				}
			}

            if($('.wallet-holder')[0] && $('.wallet-holder')[0].style.display !="none")
                $('.wallet_details').hide();

			$('.wallet-holder ul').show();
			self.$('.wallet-holder li').on('click', function(){
				var quotation_id = $(this).text();
				self.$(".wallet_input").val(quotation_id);
                $('.wallet-holder').hide();
                self.focusout_wallet_input();
			});
			if(event.which == 38){
				// Up arrow
				self.index--;
				var len = $('.wallet-holder li').length;
				if(self.index < 0)
					self.index = len-1;
				self.parent.scrollTop(36*self.index);
				updown_press = true;
			}else if(event.which == 40){
				// Down arrow
				self.index++;
				if(self.index > $('.wallet-holder li').length - 1)
					self.index = 0;
				self.parent.scrollTop(36*self.index);
			   	updown_press = true;
			}
			if(updown_press){
				$('.wallet-holder li.active').removeClass('active');
				$('.wallet-holder li').eq(self.index).addClass('active');
				$('.wallet-holder li.active').select();
			}

			if(event.which == 27){
				// Esc key
				$('.wallet-holder ul').hide();
			}else if(event.which == 13 && self.index >=0 && $('.wallet-holder li').eq(self.index)[0]){
				var selcted_li_wallet_id = $('.wallet-holder li').eq(self.index)[0].innerText;
				self.$(".wallet_input").val(selcted_li_wallet_id);
                $('.wallet-holder ul').hide();
				self.$('.wallet-holder').hide();
				self.index = -1;
                self.$('.wallet_input').focusout();

			}
        },

        focus_wallet_input: function(){
            var self = this;
			if(self.gui && self.gui.get_current_screen() == 'payment'){
				var paymentscreen = self.pos.gui.chrome.screens.payment;
				$('body').off('keypress', paymentscreen.keyboard_handler);
                $('body').off('keydown', paymentscreen.keyboard_keydown_handler);
                window.document.body.removeEventListener('keypress',paymentscreen.keyboard_handler);
                window.document.body.removeEventListener('keydown',paymentscreen.keyboard_keydown_handler);
			}
        },

        focusout_wallet_input:function(){
            var self = this;
            var wallet_input = $('.wallet_input').val();
            if(wallet_input && self.pos.db.wallet_by_name[wallet_input]){
                $('.wallet_details').show();
                var wallet = self.pos.db.wallet_by_name[wallet_input];
                $('.wallet_customer').text(wallet.partner_id[1]);
                $('.available_balance').text(self.pos.db.partner_by_id[wallet.partner_id[0]].wallet_credits);
                $('.wallet-holder').hide();
            }
            if(self.gui && self.gui.get_current_screen() == 'payment'){
                var paymentscreen = self.pos.gui.chrome.screens.payment;
                $('body').keypress(paymentscreen.keyboard_handler);
                $('body').keydown(paymentscreen.keyboard_keydown_handler);
                window.document.body.addEventListener('keypress',paymentscreen.keyboard_handler);
                window.document.body.addEventListener('keydown',paymentscreen.keyboard_keydown_handler);
			}
        },

        wk_click_cancel: function(){
            var self = this;
            self.pos.gui.close_popup();
        },

        click_validate_wallet:function(){
            var self = this;
            var wallet_input = $('.wallet_input').val();
            if(wallet_input && self.pos.db.wallet_by_name[wallet_input]){
                var wallet = self.pos.db.wallet_by_name[wallet_input];
                var partner = self.pos.db.get_partner_by_id(wallet.partner_id[0]);
                if (partner)
                    self.pos.gui.show_popup('wallet_recharge',{'partner':partner});
            }
            else{
                self.$('.wallet_input').addClass('text_shake')
                setTimeout(function(){
                    self.$('.wallet_input').removeClass('text_shake');
                },500);
            }
         }
     });
     gui.define_popup({
		name: 'wallet_recharge_by_number',
		widget: MainWalletRechargePopup
	});

//  ---add button for rechare wallet by wallet id----------------
    var WalletRechargeWidget = PosBaseWidget.extend({
		template: 'WalletRechargeWidget',
		renderElement: function(){
            var self = this;
            this._super();
            this.$el.click(function(){
                if(self.pos.db.wallet_journal)
                    self.pos.gui.show_popup("wallet_recharge_by_number");
                else
                    self.pos.gui.show_popup('wk_error_notify',{
                        title: _t('Payment Method  For Wallet Not Found'),
                        body: _t('Please check the backend configuration. No payment method for wallet is available'),
                    });
            });
        },
    });

    chrome.Chrome.prototype.widgets.unshift({
		'name':   'wallet_recharge',
		'widget': WalletRechargeWidget,
		'append':  '.pos-rightheader',
	});


    screens.ClientListScreenWidget.include({
        show: function(){
			var self = this;
			var current_order = self.pos.get_order();
			self._super();
			if(current_order != null && current_order.wallet_recharge_data){
                if(self.is_wallet_orderline())
				    self.gui.back();
                else
                    current_order.wallet_recharge_data = null;
			}
		},
// -------------------check item cart contain wallet product or not------------
        is_wallet_orderline: function(){
            var self = this;
            var current_order = self.pos.get_order();
            var wallet_line = false;
            if(current_order.get_orderlines() && self.pos.db.wallet_product){
                current_order.get_orderlines().forEach(function(orderline){
                    if(orderline.product.id == self.pos.db.wallet_product.id)
                        wallet_line = true;
                });
            }
            return wallet_line;
        },

        display_client_details: function(visibility,partner,clickpos){
            var self = this;
            self._super(visibility,partner,clickpos);

            self.$('.button.recharge_wallet').on('click',function(){
                if(self.pos.db.wallet_journal)
                    self.pos.gui.show_popup('wallet_recharge',{'partner':partner});
                else
                    self.pos.gui.show_popup('wk_error_notify',{
                        title: _t('Payment Method  For Wallet Not Found'),
                        body: _t('Please check the backend configuration. No payment method for wallet is available'),
                    });
            })
            self.$('.button.create_wallet').on('click',function(){
                if(self.pos.db.wallet_journal)
                    self.pos.gui.show_popup('create_wallet',{
                        'partner':partner,
                        'title':'No Wallet For Selected Customer',
                        'body':'You need to create a wallet for this customer before you can proceed to recharge'
                    })
                else
                    self.pos.gui.show_popup('wk_error_notify',{
                        title: _t('Payment Method  For Wallet Not Found'),
                        body: _t('Please check the backend configuration. No payment method for wallet is available'),
                    });
            })
        }
    });

   screens.PaymentScreenWidget.include({
        payment_input: function(input) {
            var self = this;
            var current_order = self.pos.get_order();
            var client = current_order.get_client();
            this._super(input);
            if($.isNumeric(input)){
                var selected_paymentline = current_order.selected_paymentline;
                if(selected_paymentline && selected_paymentline.is_wallet_payment_line){
                    var input_amount = selected_paymentline.amount;
                    selected_paymentline.amount = 0;
                    var due_amount = current_order.get_due();
                    var wallet_credits = client.wallet_credits;
                    var set_this_amount = Math.min(due_amount, wallet_credits, input_amount);
                    current_order.selected_paymentline.set_amount(set_this_amount);
                    self.inputbuffer = set_this_amount.toString();
                    self.order_changes();
                    self.render_paymentlines();
                    self.$('.paymentline.selected .edit').text(self.format_currency_no_symbol(set_this_amount));
                    $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + self.format_currency(client.wallet_credits-set_this_amount) + "</span>");
                }
            }else if (input == "BACKSPACE") {
                var selected_paymentline = current_order.selected_paymentline;
                if(selected_paymentline && selected_paymentline.is_wallet_payment_line){
                    var input_amount = selected_paymentline.amount;
                    self.$('.paymentline.selected .edit').text(self.format_currency_no_symbol(set_this_amount));
                    $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + self.format_currency(client.wallet_credits-input_amount) + "</span>");

                }
            }
        },
        check_existing_wallet_line: function(){
            var self = this;
            var current_order = self.pos.get_order();
            var existing_wallet_line = null;
            var paymentlines = current_order.get_paymentlines();
            if (self.pos.db.wallet_journal){
                paymentlines.forEach(function(line){
                    if(line.cashregister.journal.id == self.pos.db.wallet_journal.id){
                        line.is_wallet_payment_line = true;
                        existing_wallet_line = line;
                        return true;
                    }
                });
            }
            return existing_wallet_line;
        },

        click_paymentmethods: function(id) {
            var self = this;
            var cashregister = null;
            var current_order = self.pos.get_order();
            var client = current_order.get_client();
            var due = current_order.get_due();
            for ( var i = 0; i < this.pos.cashregisters.length; i++ ) {
                if ( this.pos.cashregisters[i].journal_id[0] === id ){
                    cashregister = this.pos.cashregisters[i];
                    break;
                }
            }
            if(cashregister.journal.wallet_journal){
                if(client && client.wallet_credits > 0){
                    var existing_line = self.check_existing_wallet_line();
                    var selected_paymentline = null;
                    if(existing_line){
                        current_order.select_paymentline(existing_line);
                        selected_paymentline = current_order.selected_paymentline;
                    }else if(due > 0){
                        this._super(id);
                        selected_paymentline = current_order.selected_paymentline;
                    }
                    if(selected_paymentline){
                        selected_paymentline.set_amount(0);
                        due = current_order.get_due();
                        var payment_amount = Math.min(due, client.wallet_credits);
                        selected_paymentline.set_amount(payment_amount);
                        selected_paymentline.is_wallet_payment_line = true;
                        self.render_paymentlines();
                        $('.paymentline.selected .edit').text(self.format_currency_no_symbol(payment_amount));
                        $('#use_wallet_payment').prop('checked', true);
                        self.order_changes();
                        $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + self.format_currency(client.wallet_credits-payment_amount) + "</span>");
                    }
                }
                else if(!client){
                    self.pos.gui.show_popup('confirm',{
                        'title': _t('Please select the Customer'),
                        'body': _t('You need to select the customer before using wallet payment method.'),
                        confirm: function(){
                            self.gui.show_screen('clientlist');
                        },
                    });
                }
                else if(client && !client.wallet_id){
                    self.pos.gui.show_popup('wk_error_notify',{
							title: _t('No Wallet For Selected Customer'),
							body: _t('Please configure/create a wallet from backend for the selected customer.'),
						});
                }
            }else
                this._super(id);
        },
        show: function(){
            var self = this;
            this._super();
            var current_order = self.pos.get_order();
            var client = current_order.get_client();
            self.hide_wallet_payment_method();
            if(client){
                 if(client.wallet_credits > 0 && !current_order.wallet_recharge_data && self.pos.db.wallet_journal ) {
                    self.check_existing_wallet_line();
                    $('div.wallet_balance').show();
                    $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + self.format_currency(client.wallet_credits) + "</span>");
                    $('div.use_wallet').show();
                    $('#use_wallet_payment').change(function() {
                        if($(this).is(":checked")){
                            self.click_paymentmethods(self.pos.db.wallet_journal.id);
                            if(!self.check_existing_wallet_line())
                                $('#use_wallet_payment').prop('checked', false);
                        }
                        else{
                            current_order.remove_paymentline(self.check_existing_wallet_line());
                            self.render_paymentlines();
                        }
                    });
                }else{
                    $('div.use_wallet').hide();
                     $('div.wallet_balance').hide();
                }
            }else{
                $('div.wallet_balance').hide();
                $('div.use_wallet').hide();

            }
            var existing_wallet_line = self.check_existing_wallet_line();
            if(existing_wallet_line){
                self.update_walletline_balance(existing_wallet_line);
            }
        },

        update_walletline_balance: function(pline){
            var self = this;
            var order = self.pos.get_order();
            var client = self.pos.get_order().get_client();
            if(client.wallet_credits >0){
                order.select_paymentline(pline);
                var pline_amount =  pline.amount;
                pline.set_amount(0);
                var due = self.pos.get_order().get_due();
                var payment_amount = Math.min(due, pline_amount, client.wallet_credits);
                pline.set_amount(payment_amount);
                pline.is_wallet_payment_line = true;
                self.render_paymentlines();
                $('.paymentline.selected .edit').text(self.format_currency_no_symbol(payment_amount));
                $('#use_wallet_payment').prop('checked', true);
                self.order_changes();
                $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + self.format_currency(client.wallet_credits-payment_amount) + "</span>");
            }
            else{
                order.remove_paymentline(pline);
                self.reset_input();
                self.render_paymentlines();
            }
        },

        hide_wallet_payment_method: function(){
            var self = this;
            var current_order= self.pos.get_order();
            if(current_order && self.pos.db.wallet_journal){
                var wallet_journal_id = self.pos.db.wallet_journal.id;
                var find_string = '[data-id=' + wallet_journal_id.toString() + ']';
                var wallet_paymentmethods = ($('.paymentmethods').find(find_string)[0]);
                if(current_order && current_order.wallet_recharge_data && self.pos.db.wallet_journal ||!(current_order && current_order.get_client() && current_order.get_client().wallet_credits ) )
                    $(wallet_paymentmethods).hide();
                else
                     $(wallet_paymentmethods).show();
            }
        },

        show_wallet_payment_method:function(){
            var self = this;
            var wallet_journal_id = self.pos.db.wallet_journal.id;
            var find_string = '[data-id=' + wallet_journal_id.toString() + ']';
            var wallet_paymentmethods = ($('.paymentmethods').find(find_string)[0]);
            if (wallet_paymentmethods)
                $(wallet_paymentmethods).show();

        },
    // ------update customer wallet balance--------------------
        validate_order: function(force_validation) {
            var self = this;
            var current_order= self.pos.get_order();
            self._super(force_validation);
            if(current_order && current_order.wallet_recharge_data && self.pos.db.wallet_product){
                var orderline = current_order.get_orderlines();
                var partner = current_order.get_client();
                var amount = 0.0;
                current_order.get_orderlines().forEach(function(orderline){
                    if(orderline.product.id == self.pos.db.wallet_product.id){
                        amount = amount + parseFloat(orderline.get_display_price());
                    }
                });
                partner.wallet_credits = round_di(parseFloat(partner.wallet_credits) + amount,3);
                self.pos.chrome.screens.clientlist.partner_cache.clear_node(partner.id);
            }
            else if(current_order && self.pos.db.wallet_journal && current_order.get_client()){
                var plines = current_order.get_paymentlines();
                var amount = 0.0;
                var partner = current_order.get_client();
                plines.forEach(function(pline){
                    if(pline.cashregister.journal.id == self.pos.db.wallet_journal.id){
                        amount = amount + parseFloat(pline.amount);
                    }
                });
                partner.wallet_credits = round_di(parseFloat(partner.wallet_credits) - amount,3);
                self.pos.chrome.screens.clientlist.partner_cache.clear_node(partner.id);
            }
        }
   });
});
