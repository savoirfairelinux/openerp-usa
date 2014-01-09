# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': 'CIM Transaction',
    'version': '1.3',
    'category': 'Generic Modules/Others',
    'description': """
    CIM Transactions using authorise.net
    """,
    'author': 'NovaPoint Group LLC',
    'website': ' http://www.novapointgroup.com',
    'depends': ['account_payment_ccapi_authdotnet'],
    'data': [
            'security/ir.model.access.csv',
            'wizard/edit_payment_profile_view.xml',
            'wizard/make_transaction_view.xml',
            'wizard/delete_payment_profile_view.xml',
            'wizard/create_payment_profile_view.xml',
            'cim_transaction_view.xml',
            'partner_view.xml',
            'company_view.xml',
            'account_voucher_view.xml'
    ],
    'demo': [
    ],
    'test': [
        'test/account_payment_cim_authdotnet.yml'
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
