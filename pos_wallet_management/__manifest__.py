# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "POS Wallet Management",
  "summary"              :  "This module allows the seller to store customer credits in their wallet. These credits can be used by the customer for future purchases.",
  "category"             :  "Point Of Sale",
  "version"              :  "1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-POS-Wallet-Management.html",
  "description"          :  """POS Wallet Management""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=pos_wallet_management&version=12.0",
  "depends"              :  [
                             'point_of_sale',
                             'sale',
                            ],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'wizard/pos_wallet_cancellation.xml',
                             'views/demo_product.xml',
                             'views/pos_wallet_management_view.xml',
                             'views/wallet_sequence_view.xml',
                             'views/template.xml',
                            ],
  "demo"                 :  ['data/pos_wallet_data.xml'],
  "qweb"                 :  ['static/src/xml/pos_wallet_management.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  169,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}
