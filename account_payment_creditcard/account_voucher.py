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
from openerp.tools.translate import _
import time

class AuthnetAIMError(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return str(self.parameter)

class account_voucher(osv.osv):

    def setParameter(self, parameters={}, key=None, value=None):

        if key != None and value != None and str(key).strip() != '' and str(value).strip() != '':
            parameters[key] = str(value).strip()
        else:
            raise AuthnetAIMError('Incorrect parameters passed to setParameter(): {0}:{1}'.format(key, value))
        return parameters
    
    def cancel_cc(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, { 'cc_number':'',
                                       'cc_e_d_month':'',
                                       'cc_e_d_year':'',
                                       'cc_v':'',
                                       'cc_auth_code':'',
                                       'cc_trans_id':'', })
        
    def authorize(self, cr, uid, ids, context=None):
#        self.do_transaction(cr, uid, ids,refund=False, context=context)
        return False

    def cc_refund(self, cr, uid, ids, context=None):
#        self.do_transaction(cr, uid, ids, refund=True,context=context)
        return True

    def _get_zip(self, cr, uid, ids, zip_id, context={}):
        if zip_id:
                zip_code = self.pool.get('address.zip').browse(cr, uid, zip_id)
                return zip_code.zipcode
        return ''
    
    def _get_country(self, cr, uid, ids, country_id, context={}):
          if country_id:
              country = self.pool.get('res.country').browse(cr, uid, country_id)
              return country.name
          return ''

    def _get_state(self, cr, uid, ids, state_id, context={}):
        if state_id:
              state = self.pool.get('res.country.state').browse(cr, uid, state_id)
              return state.name
        return ''

    def _get_cardholder_details(self, cr, uid, ids, partner_id, context={}):
        ret = {}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            ret = {'name':partner.name,
                'street':partner.street,
                'street2':partner.street2,
                'city':partner.city,
                'country':self._get_country(cr, uid, ids, partner.country_id.id),
                "zip":partner.zip,
                "state":self._get_state(cr, uid, ids, partner.state_id.id),
                'title':partner.title and partner.title.name
                }
        return ret

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
        result = super(account_voucher, self).create(cr, uid, vals, context)
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
        result = super(account_voucher, self).write(cr, uid, ids, vals, context)
        return result
    
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        '''
            Decrypt credit card number after reading from database and display last four digits if there is 
            no no_mask in context
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
        vals = super(account_voucher, self).read(cr, uid, ids, fields, context, load)
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
            'cc_length': 0,
            'cc_v':'',
            'cc_e_d_month':'',
            'cc_e_d_year':'',
            'cc_trans_id': '',
            'cc_status':'',
            'cc_charge':False,
            'cc_details': False,
            'is_charged':False,
            'cc_auth_code': False,
            'trans_history_ids':[]
        }
        default.update(vals)
        return super(account_voucher, self).copy(cr, uid, id, default=default, context=context)

#     def onchange_pre_authorize(self, cr, uid, ids, cc_p_authorize, context={}):
#         if cc_p_authorize:
#             return {'value':{'cc_charge':False, 'cc_p_authorize':True } }
#         return {'value':{'cc_charge':True, 'cc_p_authorize':False } }
# 
#     def onchange_cc_charge(self, cr, uid, ids, cc_charge, context={}):
#         if cc_charge:
#             return {'value':{'cc_charge':True, 'cc_p_authorize':False } }            
#         return {'value':{'cc_charge':False, 'cc_p_authorize':True } }

    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        res = super(account_voucher, self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=context)
        res['value'].update({'cc_order_amt':amount, 'cc_refund_amt':amount}) 
        return res

    _inherit = 'account.voucher'
    _columns = {
        'cc_name':fields.char("Card Holder's Name", size=32,),
        'cc_b_addr_1':fields.char('Billing Address1', size=32,),
        'cc_b_addr_2':fields.char('Billing Address2', size=32,),
        'cc_city': fields.char('City', size=32,),
        'cc_state':fields.char('State', size=32,),
        'cc_zip':fields.char('Postal/Zip', size=32,),
        'cc_country':fields.char('Country', size=32,),
        'cc_order_date':fields.date('Order Date',),
        'cc_order_amt':fields.float('Order Amt',required=True),
        'cc_number':fields.char('Credit Card Number', size=256),
        'cc_v':fields.char('Card Code Verification', size=3),
        'cc_e_d_month':fields.char('Expiration Date MM', size=32),
        'cc_e_d_year':fields.char('Expiration Date YY', size=32),
        'cc_comment':fields.char('Comment', size=128,),
        'cc_auth_code':fields.char('Authorization Code', size=32),
        'cc_save_card_details':fields.boolean('Save Credit Card details'),
        'cc_ecommerce_sale':fields.boolean('Ecommerce sale'),
        'cc_p_authorize':fields.boolean('Pre-authorize'),
        'cc_charge':fields.boolean('Charge'),
        'cc_info_hide':fields.boolean('Credit Info Hide'),
        'cc_status':fields.text('Status Message'),
        'cc_details_autofill':fields.boolean('Credit Card Details Auto Fill'),
        'cc_reseller':fields.boolean('Reseller'),
        'rel_sale_order_id':fields.many2one('sale.order', 'Related Sale Order'),
        'cc_trans_id':fields.char('Transaction ID', size=128),
        'cc_bank':fields.many2one('res.bank', 'Bank'),
        'cc_details':fields.many2one('res.partner.bank', 'Bank'),
        'cc_length':fields.integer('CC Length'),
        'cc_transaction':fields.boolean('Transaction Done'),
        'key':fields.char('Encryption Key', size=1024,
                          help="The Key used to Encrypt the Credit Card Number"),
        'cc_refund_amt':fields.float('Refund Amt'),
        'is_charged': fields.boolean('CreditCard Charged'),
        'trans_history_ids': fields.one2many('transaction.details', 'voucher_id', 'Transaction History')
    }
    _defaults = {
        'cc_info_hide': lambda * a: True,
        'cc_p_authorize': lambda * a: True,
    }

    def onchange_cc_details(self, cr, uid, ids, cc_details, context={}):
        dic = {}
        if cc_details:
            context['cc_no'] = 'no_mask'
            bank = self.pool.get('res.partner.bank').browse(cr, uid, cc_details, context=context)
            dic['cc_e_d_month'] = bank.cc_e_d_month
            dic['cc_e_d_year'] = bank.cc_e_d_year
            dic['cc_number'] = bank.cc_number
            dic['cc_v'] = bank.cc_v
        return {'value':dic}
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context={}, sale_id=False):
        if not context:
            context = {}
        if not journal_id:
            return {}
        if not partner_id:
            return {}   
        res = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)
        if not res.has_key('value'):
            res['value'] = {}
        cc_allow_refunds = jorurnal_cc_allow = False
        cardholder_details = self._get_cardholder_details(cr, uid, ids, partner_id, context=context)
        if journal_id and cardholder_details:
            journal_read = self.pool.get('account.journal').read(cr, uid, journal_id, ['cc_allow_processing','cc_allow_refunds'])
            jorurnal_cc_allow = journal_read['cc_allow_processing']
            cc_allow_refunds = journal_read['cc_allow_refunds']
            res['value']['cc_name'] = cardholder_details['name']
            res['value']['cc_b_addr_1'] = cardholder_details['street']
            res['value']['cc_b_addr_2'] = cardholder_details['street2']
            res['value']['cc_city'] = cardholder_details['city']
            res['value']['cc_country'] = cardholder_details['country']
            res['value']['cc_zip'] = cardholder_details['zip']
            res['value']['cc_state'] = cardholder_details['state']
            res['value']['cc_reseller'] = cardholder_details['title'] == 'Reseller' and True or False
            res['value']['cc_save_card_details'] = False
        
        res['value']['cc_info_hide'] = True
        if jorurnal_cc_allow:
            res['value']['cc_info_hide'] = False
        
        if cc_allow_refunds:
            res['value']['cc_info_hide'] = True
            
        context.update({'sale_id':sale_id})
        if not sale_id:
            sale_id = context.get('sale_id')
        if sale_id and res['value'].get('line_cr_ids') :
            sale = self.pool.get('sale.order').browse(cr, uid, sale_id, context=context)
            lines = []
            for line in res['value']['line_cr_ids']:
                for invoice in sale.invoice_ids:
                    if not (line.get('invoice_id') and line.get('invoice_id') and line['invoice_id'] == invoice.id):
                        line['pay'] = False
                    else:
                        line['pay'] = True
                        line['amount'] = line['amount_original']
                lines.append(line)
            res['value']['line_cr_ids'] = lines
        return res

    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')

        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'

        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_line_found = False

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        INV_IDS = []
        
        if context.get('sale_id'):
            INV_IDS = [x.id for x in self.pool.get('sale.order').browse(cr, uid, context['sale_id'], context=context).invoice_ids]
        
        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if INV_IDS:
                if line.invoice.id in INV_IDS:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_line_found = line.id
                    break
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_line_found = line.id
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_line_found = line.id
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0
        
        
        #voucher line creation
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue
            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (move_line_found == line.id) and min(abs(price), amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            inv_ids = []
            REC = False
            if line.invoice.id and context.get('sale_id'):
                if INV_IDS and line.invoice.id in INV_IDS:
                    REC = True

            if not move_line_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        if REC:
                            rs['amount'] = amount
                            total_debit -= amount
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
#                         amount = 0.0
                        if REC:
                            rs['amount'] = amount
                            total_credit -= amount
            if REC:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
        return default
    
    def _historise(self, cr, uid, id, trans_type='Pre-Auth', trans_id=False, status='', amount=0.0, context=None):
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, [id], context=context):
            vals = {
                'voucher_id':rec.id,
                'trans_id': trans_id,
                'trans_type':trans_type,
                'status':status,
                'amount':amount,
                'transaction_date':time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            self.pool.get('transaction.details').create(cr, uid, vals, context=context)
        return True

account_voucher()

class res_company(osv.osv):
    '''
    Add credit card details on company configuration
    '''
    _inherit = "res.company"
    _columns = {
        'cc_login': fields.char('CreditCard Login ID', size=64),
        'cc_transaction_key': fields.char('Transaction Key', size=64),
        'cc_testmode': fields.boolean('Test Mode'),
        'cc_journal_id':fields.many2one('account.journal', 'Payment Method', help="The default payment method on payment voucher open using the Pay button from sale order."),
    }
res_company()

class transaction_details(osv.Model):
    _name = "transaction.details"
    _rec_name = 'trans_id'
    _description = 'Transaction Details'
    _order = 'transaction_date desc'
    _columns = {
        'trans_id':fields.char('Transaction ID', size=128),
        'amount':fields.float('Amount'),
        'trans_type':fields.char('Transaction Type', size=64),
        'transaction_date':fields.datetime('Transaction Date'),
        'voucher_id':fields.many2one('account.voucher', 'Account Voucher'),
        'status':fields.char('Message', size=256),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
