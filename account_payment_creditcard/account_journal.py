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
import rsa_encrypt

class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'cc_allow_processing': fields.boolean('Allow Credit Card Processing',),
        'cc_allow_refunds': fields.boolean('Allow Credit Card Refunds',),
    }
account_journal()


class res_partner(osv.osv):
    _inherit = "res.partner"
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('bank_ids',[]) and len(vals['bank_ids'][0]) == 3 and vals['bank_ids'][0][2] :
            if vals['bank_ids'][0][2].get('cc_number',False):
                if ('XXXXXXXXX' in vals['bank_ids'][0][2]['cc_number']):
                    if vals.get('cc_number'):
                        del vals['cc_number']
        result = super(res_partner, self).write(cr, uid, ids, vals, context)
        return True

res_partner()

class res_partner_bank(osv.osv):
    '''Bank Accounts'''

    _inherit = "res.partner.bank"

    _columns = {
        'cc_number':fields.char('Credit Card Number', size=256),#Given size 256 because the credit card is stored as encrypted format.
        'cc_e_d_month':fields.char('Expiration Date MM', size=32),
        'cc_e_d_year':fields.char('Expiration Date YY', size=32),
        'cc_v':fields.char('Card Code Verification', size=3),
        'key':fields.char('Encryption Key', size=1024,
                          help="The Key used to Encrypt the Credit Card Number"),
    }
    
    def create(self, cr, uid, vals, context=None):
        """ 
            Encrypt credit card number before writing to database
            @param self : The object pointer
            @param cr: A database cursor
            @param uid: ID of the user currently logged in
            @param vals: Dictionary of Values.
            @param context: A standard dictionary
            @return:ID of newly created record.
        """
        if context is None:
            context = {}
        if vals.get('cc_number', False):
            res = rsa_encrypt.encrypt(vals.get('cc_number', False))
            res['cc_number'] = res['enc_value']
            del res['enc_value']
            vals.update(res)
        result = super(res_partner_bank, self).create(cr, uid, vals, context)
        return result
    
    def write(self, cr, uid, ids, vals, context=None):
        '''
            Encrypt credit card number before writing to database
            @param self : The object pointer
            @param cr: A database cursor
            @param uid: ID of the user currently logged in
            @param ids: List of ids selected
            @param vals: Dictionary of Values.
            @param context: A standard dictionary
            @return:True.
        '''
        if context is None:
            context = {}
        context.update({'cc_no':'no_mask'})
        if not isinstance(ids,list):
            ids = [ids]
        for record in self.browse(cr, uid, ids, context=context):
            if vals.get('cc_number', False):
                res = rsa_encrypt.encrypt(vals.get('cc_number', False), record.key)
                res['cc_number'] = res['enc_value']
                del res['enc_value']
                vals.update(res)
        result = super(res_partner_bank, self).write(cr, uid, ids, vals, context)
        return result
    
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        '''
            @param self : The object pointer
            @param cr: A database cursor
            @param uid: ID of the user currently logged in
            @param ids: List of ids selected
            @param fields: List of fields
            @param context: A standard dictionary
            @param load: a parameter used for reading the values of functional fields
            @return:List of dictionary of fields,values pair
        '''
        if context is None:
            context = {}
        if fields and 'cc_number' in fields and 'key' not in fields:
            fields.append('key')
        vals = super(res_partner_bank, self).read(cr, uid, ids, fields, context, load)
        if isinstance(vals, list):
            for val in vals:
                if val.get('cc_number', False) :
                    dec_data = rsa_encrypt.decrypt(val.get('cc_number', False), val.get('key', ''))
                    val['cc_number'] = dec_data
                    if context.get('cc_no', '') != 'no_mask':
                        i = len(val['cc_number']) - 4
                        val['cc_number'] = 'X' * i + val['cc_number'][-4:len(val['cc_number'])]
        else:
            if vals.get('cc_number', False) :
                    dec_data = rsa_encrypt.decrypt(vals.get('cc_number', False), vals.get('key', ''))
                    vals['cc_number'] = dec_data
                    if context.get('cc_no', '') != 'no_mask':
                        i = len(vals['cc_number']) - 4
                        vals['cc_number'] = 'X' * i + vals['cc_number'][-4:len(vals)]
        return vals

    def copy(self, cr, uid, id, default=None, context=None):
        """Overrides orm copy method
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of case’s IDs
        @param context: A standard dictionary for contextual values
        """
        if default is None:
            default = {}
        vals = {
            'cc_number': '',
            'cc_v':'',
            'cc_e_d_month':'',
            'cc_e_d_year':'',
        }
        default.update(vals)
        return super(res_partner_bank, self).copy(cr, uid, id, default=default, context=context)
    
res_partner_bank()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: