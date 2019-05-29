odoo.define('strategiksv.openwindows', function (require) {
"use strict";

var form_widget = require('web.form_widgets');
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;

form_widget.WidgetButton.include({
    on_click: function() {
         if(this.node.attrs.custom === "click_invoice"){
            var x=document.getElementById('identidad').children[0].innerHTML;
            var r=document.getElementById('reporte').children[0].innerHTML;
            window.open(location.protocol + '//' + location.hostname+'/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&j_acegi_security_check?&j_username=strategik&j_password=strategik&userLocale=es_SV&_flowId=viewReportFlow&ParentFolderUri=/Strategik_reports/contabilidad/trasacciones&reportUnit=/Strategik_reports/contabilidad/trasacciones/'+r+'&decorate=no&output=pdf&facturaId='+x);
            return;
         }
         if(this.node.attrs.custom === "click_partida"){
            var x=document.getElementById('identidad').children[0].innerHTML;
            window.open(location.protocol + '//' + location.hostname+'/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&j_acegi_security_check?&j_username=strategik&j_password=strategik&userLocale=es_SV&_flowId=viewReportFlow&ParentFolderUri=/Strategik_reports/contabilidad/trasacciones&reportUnit=/Strategik_reports/contabilidad/trasacciones/Partida&decorate=no&PatidaId='+x);
            return;
         }
         if(this.node.attrs.custom === "click_venta"){
            var x=document.getElementById('identidad').children[0].innerHTML;
            window.open(location.protocol + '//' + location.hostname+'/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&j_acegi_security_check?&j_username=strategik&j_password=strategik&userLocale=es_SV&_flowId=viewReportFlow&ParentFolderUri=/Strategik_reports/contabilidad/trasacciones&reportUnit=/Strategik_reports/contabilidad/trasacciones/BoletaDeVenta&decorate=no&output=pdf&documentid='+x);
            return;
         }
         if(this.node.attrs.custom === "click_cheque"){
            var x=document.getElementById('identidad').children[0].innerHTML;
            var r=document.getElementById('reporte').children[0].innerHTML;
            window.open(location.protocol + '//' + location.hostname+'/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&j_acegi_security_check?&j_username=strategik&j_password=strategik&userLocale=es_SV&_flowId=viewReportFlow&ParentFolderUri=/Strategik_reports/contabilidad/trasacciones&reportUnit=/Strategik_reports/contabilidad/trasacciones/'+r+'&decorate=no&output=pdf&chequeId='+x);
            return;
         }
         if(this.node.attrs.custom === "click_caja"){
            var x=document.getElementById('identidad').children[0].innerHTML;
            window.open(location.protocol + '//' + location.hostname+'/jasperserver/flow.html?_flowId=viewReportFlow&standAlone=true&j_acegi_security_check?&j_username=strategik&j_password=strategik&userLocale=es_SV&_flowId=viewReportFlow&ParentFolderUri=/Strategik_reports/contabilidad/trasacciones&reportUnit=/Strategik_reports/contabilidad/trasacciones/Caja&decorate=no&cajaid='+x);
            return;
         }
         this._super();
    },
});
});
