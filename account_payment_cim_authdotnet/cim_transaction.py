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
from openerp.osv import osv, fields

class cust_profile(osv.Model):
    _name = "cust.profile"
    _description = 'Customer Profile'
    _columns = {
        'name':  fields.char('Name', size=128, required=True, help='Store payment profile id', readonly=True),
        'payment_profile_ids':fields.one2many('cust.payment.profile', 'cust_profile_id', 'Payment Profiles' , help='Store customers payment profile id', readonly=True),
        'shipping_address_id' : fields.char('Shipping Address Request ID')
    }

class cust_payment_profile(osv.Model):
    _name = "cust.payment.profile"
    _description = 'Customer Payment Profile'

    def _get_partner(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('active_id', False)

    _columns = {
        'name':  fields.char('Name', size=128, required=True, help='Store payment profile id returned from authorize', readonly=True),
        'cust_profile_id':fields.many2one('cust.profile', 'Customer Profiles', help='Store customers payment profile id', readonly=True),
        'address_id':fields.many2one('res.partner', 'Address', readonly=True),
        'transaction_history_ids':fields.one2many('transaction.history', 'payment_profile_id', 'Transaction History' , help='Store History of Transactions', readonly=True),
        'description':fields.char('Description', size=128, readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', readonly=True, required=True),
        'use_default':fields.boolean('Use Default'),
        'cc_number':fields.char('Credit Card Number', size=4, required=True),
        'cc_card_type' :fields.selection([('Discovery','Discovery'),
                                          ('AMEX','AMEX'),
                                          ('MasterCard','MasterCard'),
                                          ('Visa','Visa')],'Credit Card Type')
    }

    _defaults = {
        'use_default':False,
        'partner_id': _get_partner,
    }

    def set_default(self, cr, uid, ids, context=None):
        cus_pay_obj = self.pool.get('cust.payment.profile')
        cus_pay_prof_ids = cus_pay_obj.browse(cr, uid, ids[0])
        c_ids = cus_pay_prof_ids.cust_profile_id.payment_profile_ids
        for payment_profile_obj in c_ids:
            vals = {'use_default':False}
            if payment_profile_obj.id == ids[0]:
                vals = {'use_default':True}
            cus_pay_obj.write(cr, uid, [payment_profile_obj.id], vals)
        return True

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context and (context.get('make_transaction') or context.get('edit_payment_profile')):
            cust_obj = context.get('active_model')
            pay_ids = []
            if cust_obj == 'res.partner':
                partner = self.pool.get(cust_obj).browse(cr, uid, context.get('active_id'))
                pay_profile_objs = partner.payment_profile_id.payment_profile_ids
                for pay_prof in pay_profile_objs:
                    pay_ids.append(pay_prof.id)
                if len(pay_ids) > 0:
                    args = [('id', 'in', pay_ids)]

        return super(cust_payment_profile, self).search(cr, uid, args, offset, limit, order, context, count)

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result = []
        for rec in self.browse(cr, uid, ids, context=context):
            Name = rec.name
            if rec.cc_card_type:
                Name += ' - ' + rec.cc_card_type
            if rec.cc_number:
                Name += ' - ' + rec.cc_number
            result.append((rec.id, Name))
        return result

class auth_config(osv.Model):
    _name = "auth.config"
    _rec_name = 'url'
    _description = 'Auth Configuration'
    _columns = {
        'url':fields.char('URL', size=512, required=True, help='Authorize url'),
        'url_test':fields.char('URL(Test Server) ', size=512, required=True, help='Authorize url'),
        'test_mode':fields.boolean('Test Mode'),
        'url_extension':fields.char('URL Extension', size=512, required=True, help='Authorize url extension'),
        'xsd_link':fields.char('XSD Link', size=512, required=True, help='Path of the file containing the schema definitions for the request'),
        'transaction_key':fields.char('Transaction Key', size=64, required=True,),
        'login_id':fields.char('CreditCard Login ID', size=64, required=True,),
    }

class transaction_history(osv.Model):
    _name = "transaction.history"
    _rec_name = 'trans_id'
    _description = 'Transaction History'
    _columns = {
        'trans_id':fields.char('Transaction ID', size=128, required=True,),
        'amount':fields.float('Amount'),
        'trans_type':fields.char('Transaction Type', size=64, required=True,),
        'transaction_date':fields.datetime('Transaction Date'),
        'payment_profile_id':fields.many2one('cust.payment.profile', 'Payment Profile ID', help='Store customers payment profile id')
    }

class transaction_details(osv.Model):
    _inherit = "transaction.details"
    _columns = {
        'payment_profile_id':fields.many2one('cust.payment.profile', 'Payment Profile ID', help='Store customers payment profile id'),
    }

#class cust_profile(osv.Model):
#    _inherit = "cust.profile"
#    _description = 'Customer Profile'
#    _columns = {
#        'payment_profile_ids':fields.one2many('cust.payment.profile', 'cust_profile_id','Payment Profiles' ,help='Store customers payment profile id'),
#    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
