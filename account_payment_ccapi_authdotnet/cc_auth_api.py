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
import socket
import sys
import urllib
import collections
from time import time
from openerp.tools.translate import _
import base64
from openerp import netsvc
from openerp.addons.account_payment_creditcard import rsa_encrypt

class AuthnetAIMError(Exception):
    '''
    Class to display exceptions
    '''
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return str(self.parameter)
    def setParameter(self, parameters={}, key=None, value=None):

        if key != None and value != None and str(key).strip() != '' and str(value).strip() != '':
            parameters[key] = str(value).strip()
        else:
            raise AuthnetAIMError('Incorrect parameters passed to setParameter(): {0}:{1}'.format(key, value))
        return parameters

class auth_net_cc_api(osv.osv):
    _name = "auth.net.cc.api"
    '''
        Class to do credit card transaction
    '''
    
    def _get_prod_acc(self, product_id, journal_obj, context=False):
        if product_id and product_id.property_account_income:
            return product_id.property_account_income.id
        elif product_id and product_id.categ_id.property_account_income_categ:
             return product_id.categ_id.property_account_income_categ.id
        else:
            if journal_obj.default_credit_account_id:
                return journal_obj.default_credit_account_id.id
        return False

    def validate_sales_reciept(self, cr, uid, ids, context={}):
        voucher_obj = self.pool.get('account.voucher')
        ids = ids
        if type(ids) != type([]):
            ids = [ids]
        voucher_objs = voucher_obj.browse(cr, uid, ids, context=context)
        
        for voucher_obj in voucher_objs:
            rel_sale_order_id = voucher_obj.rel_sale_order_id.id
            sale_reciepts_ids = voucher_obj.search(cr, uid, [('type', '=', 'sale'), ('rel_sale_order_id', '=', rel_sale_order_id), ('state', 'in', ['draft'])])
            
            if not sale_reciepts_ids:
                sale_reciepts_id = self.pool.get('sale.order').create_sales_reciept(cr, uid, [rel_sale_order_id], context=context)
                sale_reciepts_ids = [sale_reciepts_id]
            voucher_obj.action_move_line_create(cr, uid, sale_reciepts_ids, context=context)
        return True

    def _get_prod_deb_acc(self, product_id, journal_obj, context=False):
        if product_id and product_id.property_account_income:
            return product_id.property_account_expense.id
        elif product_id and product_id.categ_id.property_account_expense_categ:
             return product_id.categ_id.property_account_expense_categ.id
        else:
            if journal_obj.default_debit_account_id:
                return journal_obj.default_debit_account_id.id
        return False
    
    def cancel_sales_reciept(self, cr, uid, ids, context={}):
        voucher_obj = self.pool.get('account.voucher')
        sale_obj = self.browse(cr, uid, ids, context=context)
#        vals={}
#        cr_ids_list = []
#        cr_ids = {}
        sales_receipt_ids = voucher_obj.search(cr, uid, [('rel_sale_order_id', '=', ids), ('state', '=', 'posted')], context=context)
        if sales_receipt_ids:
            voucher_obj.cancel_voucher(cr, uid, sales_receipt_ids, context=context)
#        journal_ids = self.pool.get('account.journal').search(cr,uid,[('type','=','sale_refund')])
#        if journal_ids:
#            vals['journal_id'] = journal_ids[0]
#            journal_obj = self.pool.get('account.journal').browse(cr,uid,journal_ids[0])
#            if sale_obj and sale_obj.order_line:
#                for sale_line in sale_obj.order_line:
#                    cr_ids['account_id'] = self._get_prod_deb_acc(sale_line.product_id and sale_line.product_id, journal_obj)#journal_obj.default_debit_account_id.id #Change this account to product's income account
#                    cr_ids['amount'] = sale_line.price_subtotal
#                    cr_ids['partner_id'] = sale_obj.partner_id.id
#                    cr_ids['name'] = sale_line.name
#                    cr_ids_list.append(cr_ids.copy())
#            if sale_obj.shipcharge and sale_obj.ship_method_id and sale_obj.ship_method_id.account_id:
#                cr_ids['account_id'] = sale_obj.ship_method_id.account_id.id
#                cr_ids['amount'] = sale_obj.shipcharge
#                cr_ids['partner_id'] = sale_obj.partner_id.id
#                cr_ids['name'] = 'Shipping Charge for %s'%sale_line.name
#                cr_ids_list.append(cr_ids.copy())
#                
#
#        else:
#            vals['journal_id'] = False
#        vals['partner_id'] = sale_obj.partner_id.id
#        vals['date'] = sale_obj.date_order
#        vals['rel_sale_order_id'] = ids[0]
#        vals['name'] = 'Auto generated Sales Receipt'
#        vals['type'] = 'sale'
#        vals['currency_id'] = journal_obj.company_id.currency_id.id
#        vals['line_cr_ids'] = [(0,0,cr_ids) for cr_ids in cr_ids_list]
##        vals['narration'] = voucher_obj.narration
#        vals['pay_now'] = 'pay_now'
#        vals['account_id'] = journal_obj.default_debit_account_id.id  
##        vals['reference'] = voucher_obj.reference
##        vals['tax_id'] = voucher_obj.tax_id.id
#        vals['amount'] = sale_obj.amount_total
#        vals['company_id'] = journal_obj.company_id.id
#        voucher_id = self.pool.get('account.voucher').create(cr,uid,vals,context)
        return True
     
    def do_this_transaction(self, cr, uid, ids, refund=False, context=None):
        '''
        Do credit card transaction
        '''
        ret = False
        voucher_obj = self.pool.get('account.voucher')
        partner_bank_obj = self.pool.get('res.partner.bank')
        
        wf_service = netsvc.LocalService("workflow")
        if type([]) == type(ids):
            acc_voucher_obj = voucher_obj.browse(cr, uid, ids[0], context={'cc_no':'no_mask'})
        else:
            acc_voucher_obj = voucher_obj.browse(cr, uid, ids, context={'cc_no':'no_mask'})
        user = self.pool.get('res.users').browse(cr, uid, uid)
        
        creditcard = acc_voucher_obj.cc_number#  CREDIT CARD NUMBER
        expiration = acc_voucher_obj.cc_e_d_month + acc_voucher_obj.cc_e_d_year ################ EXPIRATION DATE MM + YY
        total = acc_voucher_obj.cc_order_amt ############## ORDER AMOUNT
        
        if acc_voucher_obj.cc_save_card_details:
            if not acc_voucher_obj.cc_bank:
                raise osv.except_osv(_('No Bank selected!'), _("Please select the bank to save credit card details on customer bank details."))
            else:
                if not partner_bank_obj.search(cr, uid, [('cc_number', '=', creditcard), ('partner_id', '=', acc_voucher_obj.partner_id.id)]):
                    state_id = country_id = False
                    if acc_voucher_obj.cc_state:
                        state_ids = self.pool.get('res.country.state').search(cr, uid, [('name','=',acc_voucher_obj.cc_state)])
                        state_id = state_ids and state_ids[0] or False
                    if acc_voucher_obj.cc_country:
                        country_ids = self.pool.get('res.country').search(cr, uid, [('name','=',acc_voucher_obj.cc_country)])
                        country_id = country_ids and country_ids[0] or False
                    part = acc_voucher_obj.partner_id.id
                    if acc_voucher_obj.partner_id.parent_id:
                        part = acc_voucher_obj.partner_id.parent_id.id
                    partner_bank_obj.create(cr, uid, {'state':'bank',
                                                        'acc_number':creditcard[-4:],
                                                        'cc_number':creditcard,
                                                        'cc_e_d_month':acc_voucher_obj.cc_e_d_month,
                                                        'cc_e_d_year':acc_voucher_obj.cc_e_d_year,
                                                        'partner_id':part,
                                                        'bank':acc_voucher_obj.cc_bank.id,
                                                        'cc_v':acc_voucher_obj.cc_v,
                                                        'owner_name':acc_voucher_obj.cc_name,
                                                        'street':str(acc_voucher_obj.cc_b_addr_1) +'-'+ str(acc_voucher_obj.cc_b_addr_2),
                                                        'city': acc_voucher_obj.cc_city,
                                                        'zip': acc_voucher_obj.cc_zip,
                                                        'state_id': state_id,
                                                        'country_id': country_id
                                                    })
                    
        if refund:
            x_type = 'CREDIT'
            total = acc_voucher_obj.cc_refund_amt
            if not acc_voucher_obj.cc_trans_id:
                raise osv.except_osv(_('No Transaction ID!'), _(" Unable to find transaction id for refund."))
#             if not acc_voucher_obj.journal_id.cc_allow_refunds:
#                 raise osv.except_osv(_('Unable to do Refund!'), _("Please check \"Allow Credit Card Refunds\" on journal to do refund."))
        
        elif acc_voucher_obj.cc_p_authorize:
            x_type = 'AUTH_ONLY'
        
#         elif acc_voucher_obj.cc_charge and acc_voucher_obj.cc_auth_code:
#             x_type = 'CAPTURE_ONLY'
        
        elif acc_voucher_obj.cc_charge:
            x_type = 'PRIOR_AUTH_CAPTURE'
            if not acc_voucher_obj.cc_trans_id:
                raise osv.except_osv(_('No Transaction ID!'), _("Cannot proceed to Charge, please pre-authorize the transaction first!!"))
        else:
            raise osv.except_osv(_('No "Type of transaction"!'), _("No Transaction type selected. Please select pre-authorize or charge from \"Type of transaction\" section."))

        cvv = None
        if acc_voucher_obj.cc_v:
            cvv = acc_voucher_obj.cc_v
        tax = '0.00'
        login = user.company_id.cc_login
        transkey = user.company_id.cc_transaction_key
        testmode = user.company_id.cc_testmode

        if str(login).strip() == '' or login == None:
            raise osv.except_osv(_('Error'), _("No login name provided"))
            #raise AuthnetAIMError('No login name provided')
        if str(transkey).strip() == '' or transkey == None:
            raise osv.except_osv(_('Error'), _("No transaction key provided"))
            #raise AuthnetAIMError('No transaction key provided')
        if testmode != True and testmode != False:
            raise osv.except_osv(_('Error'), _("Invalid value for testmode. Must be True or False. "))
            #raise AuthnetAIMError('Invalid value for testmode. Must be True or False. "{0}" given.'.format(testmode))

        parameters = {}
        proxy = None
        delimiter = '|'
        results = []
        error = True
        success = False
        declined = False

        ############ initialize
        parameters = {}
        parameters = voucher_obj.setParameter(parameters, 'x_delim_data', 'true')
        parameters = voucher_obj.setParameter(parameters, 'x_delim_char', delimiter)
        parameters = voucher_obj.setParameter(parameters, 'x_relay_response', 'FALSE')
        parameters = voucher_obj.setParameter(parameters, 'x_url', 'FALSE')
        parameters = voucher_obj.setParameter(parameters, 'x_version', '3.1')
        parameters = voucher_obj.setParameter(parameters, 'x_method', 'CC')
        parameters = voucher_obj.setParameter(parameters, 'x_type', x_type)
        parameters = voucher_obj.setParameter(parameters, 'x_login', login)
        parameters = voucher_obj.setParameter(parameters, 'x_tran_key', transkey)
        
        if acc_voucher_obj.cc_charge and x_type !='CREDIT':
            parameters = voucher_obj.setParameter(parameters, 'x_auth_code', acc_voucher_obj.cc_auth_code)

        #PreAuth is done, so sending x_trans_id for capture
        if x_type in ['PRIOR_AUTH_CAPTURE','CREDIT']:
            parameters = voucher_obj.setParameter(parameters, 'x_trans_id', acc_voucher_obj.cc_trans_id)
        
        ########## setTransaction
        if str(creditcard).strip() == '' or creditcard == None:
            raise osv.except_osv(_('Error'), _("No credit card number passed to setTransaction()"))
            #raise AuthnetAIMError('No credit card number passed to setTransaction(): {0}').format(creditcard)
        if str(expiration).strip() == '' or expiration == None:
            raise osv.except_osv(_('Error'), _("No expiration number to setTransaction()"))
            #raise AuthnetAIMError('No expiration number to setTransaction(): {0}').format(expiration)
        if str(total).strip() == '' or total == None:
            raise osv.except_osv(_('Error'), _("No total amount passed to setTransaction()"))

            #raise AuthnetAIMError('No total amount passed to setTransaction(): {0}').format(total)

        parameters = voucher_obj.setParameter(parameters, 'x_card_num', creditcard)
        parameters = voucher_obj.setParameter(parameters, 'x_exp_date', expiration)
        parameters = voucher_obj.setParameter(parameters, 'x_amount', total)
        if cvv != None:
            parameters = voucher_obj.setParameter(parameters, 'x_card_code', cvv)
        if tax != None:
            parameters = voucher_obj.setParameter(parameters, 'x_tax', tax)

        ##################initialize
        parameters = voucher_obj.setParameter(parameters, 'x_duplicate_window', 180)
        parameters = acc_voucher_obj.cc_name and voucher_obj.setParameter(parameters, 'x_first_name', acc_voucher_obj.cc_name or None) or parameters
        parameters = acc_voucher_obj.cc_b_addr_1 and voucher_obj.setParameter(parameters, 'x_address', acc_voucher_obj.cc_b_addr_1 or None) or parameters
        parameters = acc_voucher_obj.cc_city and voucher_obj.setParameter(parameters, 'x_city', acc_voucher_obj.cc_city or None) or parameters
        parameters = acc_voucher_obj.cc_state and voucher_obj.setParameter(parameters, 'x_state', acc_voucher_obj.cc_state or None) or parameters
        parameters = acc_voucher_obj.cc_zip and voucher_obj.setParameter(parameters, 'x_zip', acc_voucher_obj.cc_zip or None) or parameters
        parameters = acc_voucher_obj.cc_country and voucher_obj.setParameter(parameters, 'x_country', acc_voucher_obj.cc_country or None) or parameters
        parameters = voucher_obj.setParameter(parameters, 'x_customer_ip', socket.gethostbyname(socket.gethostname()))

    #           Actual Processing
        encoded_args = urllib.urlencode(parameters)
        url = 'https://secure.authorize.net/gateway/transact.dll'
        if testmode:
            url = 'https://test.authorize.net/gateway/transact.dll'
            
        results += str(urllib.urlopen(url, encoded_args).read()).split(delimiter)

#        Results = collections.namedtuple('Results', 'ResponseCode ResponseSubcode ResponseReasonCode ResponseText AuthCode \
#                                          AVSResponse TransactionID InvoiceNumber Description Amount PaymentMethod \
#                                          TransactionType CustomerID CHFirstName CHLastName Company BillingAddress \
#                                          BillingCity BillingState BillingZip BillingCountry Phone Fax Email ShippingFirstName \
#                                          ShippingLastName ShippingCompany ShippingAddress ShippingCity ShippingState \
#                                          ShippingZip ShippingCountry TaxAmount DutyAmount FreightAmount TaxExemptFlag \
#                                          PONumber MD5Hash CVVResponse CAVVResponse')
#        response = Results(*tuple(r for r in results)[0:40])

        if results[0] == '1' and acc_voucher_obj.rel_sale_order_id and acc_voucher_obj.rel_sale_order_id.id:
            
            if acc_voucher_obj.rel_sale_order_id.state == 'done':
                so_vals = {'cc_pre_auth':True, 'rel_account_voucher_id':acc_voucher_obj.id}
            else:
                so_vals = {'state':'cc_auth', 'cc_pre_auth':True, 'rel_account_voucher_id':acc_voucher_obj.id}
            self.pool.get('sale.order').write(cr, uid, [acc_voucher_obj.rel_sale_order_id.id], so_vals)

        ret_dic = {}
        if x_type == 'AUTH_ONLY':
             status = 'Authorization: ' + str(results[3])
             ret_dic.update({
                        'cc_status' :status,
                        'cc_auth_code':results[4],
                        'cc_trans_id':results[6]
             })
             voucher_obj.write(cr, uid, ids, ret_dic)
             voucher_obj._historise(cr, uid, acc_voucher_obj.id, 'Authorization', trans_id=results[6], status=status, amount=total)
#         if x_type == 'CAPTURE_ONLY':
#             status = "Capture: " + str(results[3])
#             ret_dic['cc_status'] = status
#             voucher_obj.write(cr, uid, ids, ret_dic)
             
        elif x_type == 'PRIOR_AUTH_CAPTURE':
             status = 'Prior Authorization and Capture: ' + str(results[3])
             ret_dic['amount'] = acc_voucher_obj.cc_order_amt
             ret_dic['cc_status'] = status
             ret_dic['cc_trans_id'] = results[6]
             ret_dic['cc_transaction'] = True
             voucher_obj.write(cr, uid, ids, ret_dic)
             voucher_obj._historise(cr, uid, acc_voucher_obj.id, 'Capture',trans_id=results[6], status=status, amount=acc_voucher_obj.cc_order_amt)
             cr.commit()
             if results[0] == '1':
                 '''
                     Validating sales receipt
                 '''
                 #self.validate_sales_reciept(cr, uid, ids, context=context)
                 '''
                     Posting payment voucher
                 '''
                 voucher_obj.action_move_line_create(cr, uid, ids, context)
                 ret = True
                 voucher_obj.write(cr, uid, ids, {'is_charged':True}, context=context)
             
        elif x_type == 'CREDIT':
            status = 'Refund: ' + str(results[3])
            ret_dic['cc_status'] = status
            voucher_obj._historise(cr, uid, acc_voucher_obj.id, 'Refund',trans_id=results[6], status=status, amount=acc_voucher_obj.cc_refund_amt)
            if results[0] == '1':
                ret_dic['cc_transaction'] = False
                #Domain : [('type','=','out_refund')]
                #Context: {'type':'out_refund', 'journal_type': 'sale_refund'}
                refund_journal_id = False
                j_ids = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'sale_refund')], context=context)
                if j_ids:
                    refund_journal_id = j_ids[0]
                if refund_journal_id and context.get('cc_refund'):
                    invoice_obj = self.pool.get('account.invoice')
                    invoice_line_obj = self.pool.get('account.invoice.line')
                    inv_vals = {
                                    'type'      : 'out_refund',
                                    'journal_id': refund_journal_id,
                                    'partner_id': acc_voucher_obj.partner_id.id,
#                                    'shipcharge': context.get('cc_ship_refund'),
#                                    'ship_method_id' : context.get('ship_method_id')
                                }
#                    if context.get('ship_method_id'):
#                        ship_method = self.pool.get('shipping.rate.config').browse(cr, uid, context.get('ship_method_id'), context=context)
#                        inv_vals['sale_account_id'] = ship_method.account_id and ship_method.account_id.id,
                    inv_vals.update(invoice_obj.onchange_partner_id(cr, uid, [], 'out_refund', acc_voucher_obj.partner_id.id, '', '', '', '')['value'])
                    inv_lines = []
                    refund_lines = context.get('cc_refund',[])
                    for line in refund_lines:
                        
                        inv_line_vals = {
                            'quantity' : line['qty'],
                            'product_id' : line['product_id'],
                        }
                        onchage_vals = invoice_line_obj.product_id_change(cr, uid, [], line['product_id'], False, line['qty'], '', 'out_refund', inv_vals['partner_id'], context={})['value']
                        onchage_vals['price_unit'] = line['price_unit']
                        inv_line_vals.update(onchage_vals)
                        inv_lines.append((0, 0, inv_line_vals))
                    
                    inv_vals['invoice_line'] = inv_lines
                    
                    invoice_id = invoice_obj.create(cr, uid, inv_vals, context=context)
                    wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
                    
#                ret = True
#                voucher_obj = self.pool.get('account.voucher')
#                
#
#                refund_journal_id = False
#                if user.company_id.cc_refund_journal_id:                    
#                    refund_journal_id = user.company_id.cc_refund_journal_id.id
#                else
#                    j_ids = self.pool.get('account.journal').search(cr, uid, [('type','=','sale_refund')], context=context)
#                    if j_ids:
#                        refund_journal_id = j_ids[0]
#                
#                account_id=False
#                if refund_journal_id:
#                    default_debit_account_id = self.pool.get('account.journal').browse(cr, uid, refund_journal_id,context=context).default_debit_account_id.id
#                
#                
#                vals1 = {
#                        
#                            'name' :  'Refund : ' + (acc_voucher_obj.rel_sale_order_id and str(acc_voucher_obj.rel_sale_order_id.name) or ''),
#                            'account_id' :  default_debit_account_id,
#                            'partner_id' : acc_voucher_obj.partner_id.id,
#                            'amount'    : acc_voucher_obj.cc_order_amt,
#                            'currency_id' :  user.company_id.currency_id.id,
#                            'origin':acc_voucher_obj.rel_sale_order_id and acc_voucher_obj.rel_sale_order_id.name or ''
#                        }
#
#                
#                vals  = voucher_obj.onchange_partner_id(cr, uid, [], acc_voucher_obj.partner_id.id, refund_journal_id , acc_voucher_obj.cc_order_amt , user.company_id.currency_id.id, 'sale', time())
#                
#                vals.update(vals1)
#                
#                vals['journal_id'] = refund_journal_id
#                vals['type'] = 'sale'
#                
#               
#                
#                
#                voucher_id = voucher_obj.create(cr, uid, vals, context=context)
#                
#                
#                if acc_voucher_obj.cc_order_amt == acc_voucher_obj.rel_sale_order_id.amount_total and acc_voucher_obj.rel_sale_order_id.shipcharge:
#                    self.pool.get('sale.order').write(cr, uid, [acc_voucher_obj.rel_sale_order_id.id],{'cc_ship_refund':True},context=context)
#                    
#                refund_voucher=False
#                if 'cc_refund' not in context:
#                    refund_voucher=True
#                    sales_receipt_ids = voucher_obj.search(cr,uid,[('rel_sale_order_id','=',acc_voucher_obj.rel_sale_order_id.id),('state','=','posted'),('type','=','sale')], order="id desc",context=context)
#
#                    for receipt in voucher_obj.browse(cr, uid, sales_receipt_ids, context):
#                        
#                        for line in receipt.line_ids:
#
#                            if line.amount:
#                                vals = {
#                                            'voucher_id': voucher_id,
#                                            'name' : line.name,
#                                            'account_id' : line.account_id.id,
#                                            'partner_id' : line.partner_id.id,
#                                            'amount' : line.amount,
#                                            'type': line.type,
#                                            
#                                    }
#                                line_id = self.pool.get('account.voucher.line').create(cr, uid, vals, context)
#                        break
#                else:
#                    for line in context['cc_refund']:
#                        product=self.pool.get('product.product').browse(cr, uid, line['product_id'],context)
#                        
#                        vals = {
#                                'voucher_id': voucher_id,
#                                'name' : product.name,
#                                'account_id' : product.product_tmpl_id.property_account_income.id,
#                                'partner_id' : acc_voucher_obj.partner_id.id,
#                                'amount'    :  product.list_price * line['qty'],
#                                'type' : 'cr',                                
#                                }
#                        line_id = self.pool.get('account.voucher.line').create(cr, uid, vals, context)
#                    if context.get('cc_ship_refund'):
#                        vals = {
#                                'voucher_id': voucher_id,
#                                'name' : 'Shipping Charges of ' + acc_voucher_obj.rel_sale_order_id.name,
#                                'account_id' : acc_voucher_obj.rel_sale_order_id.ship_method_id and acc_voucher_obj.rel_sale_order_id.ship_method_id.account_id.id or False,
#                                'partner_id' : acc_voucher_obj.partner_id.id,
#                                'amount'    : context['cc_ship_refund'],
#                                'type' : 'cr', 
#                                }
#                        line_id = self.pool.get('account.voucher.line').create(cr, uid, vals, context)
#                        self.pool.get('sale.order').write(cr, uid, [acc_voucher_obj.rel_sale_order_id.id],{'cc_ship_refund':True},context=context)
#                
#                #         if x_type == 'CAPTURE_ONLY':
#             status = "Capture: " + str(results[3])
#             ret_dic['cc_status'] = status
#             voucher_obj.write(cr, uid, ids, ret_dic)
#                if not refund_voucher:      
#                    wf_service = netsvc.LocalService('workflow')
#                    wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
                
            else:
                ret_dic['cc_transaction'] = True
            voucher_obj.write(cr, uid, ids, ret_dic)
        else:
            status = ''

        return ret

auth_net_cc_api()

class account_voucher(osv.osv):

    _inherit = 'account.voucher'
    '''
        Add function to hook methods authorize and cc_refund which is added on account_payment_creditcard module
    '''
    
    def check_transaction(self, cr, uid, ids, context=None):
        transaction_record = self.browse( cr, uid, ids,context)
        for record in transaction_record:
             if record.cc_p_authorize and record.cc_auth_code:
                 raise osv.except_osv(_('Error'), _("Already Authorized!"))
             if record.cc_charge and not record.cc_auth_code:
                 raise osv.except_osv(_('Error'), _("Pre-Authorize the transaction first!"))
        return True

    def authorize(self, cr, uid, ids, context=None):
        self.check_transaction(cr, uid, ids, context)
        res = self.pool.get('auth.net.cc.api').do_this_transaction(cr, uid, ids, refund=False, context=context)
        if res:
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'account.voucher', ids[0], 'proforma_voucher', cr)
        return True
    
    def cc_refund(self, cr, uid, ids, context=None):
        return self.pool.get('auth.net.cc.api').do_this_transaction(cr, uid, ids, refund=True, context=context)
    
account_voucher()

class sale_order(osv.osv):
    _inherit = "sale.order"

    def _get_prod_acc(self, product_id, journal_obj, context=False):
        if product_id and product_id.property_account_income:
            return product_id.property_account_income.id
        elif product_id and product_id.categ_id.property_account_income_categ:
             return product_id.categ_id.property_account_income_categ.id
        else:
            if journal_obj.default_credit_account_id:
                return journal_obj.default_credit_account_id.id
        return False
    
    def create_sales_reciept(self, cr, uid, ids, context={}):
        sale_obj = self.browse(cr, uid, ids[0], context=context)
        vals = {}
        cr_ids_list = []
        cr_ids = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'sale')])
        if journal_ids:
            vals['journal_id'] = journal_ids[0]
            journal_obj = self.pool.get('account.journal').browse(cr, uid, journal_ids[0])
            if sale_obj and sale_obj.order_line:
                for sale_line in sale_obj.order_line:
                    cr_ids['account_id'] = self._get_prod_acc(sale_line.product_id and sale_line.product_id, journal_obj)#journal_obj.default_debit_account_id.id #Change this account to product's income account
                    cr_ids['amount'] = sale_line.price_subtotal
                    cr_ids['partner_id'] = sale_obj.partner_id.id
                    cr_ids['name'] = sale_line.name
                    cr_ids_list.append(cr_ids.copy())
            if sale_obj and sale_obj.shipcharge and sale_obj.ship_method_id and sale_obj.ship_method_id.account_id:
                cr_ids['account_id'] = sale_obj.ship_method_id.account_id.id
                cr_ids['amount'] = sale_obj.shipcharge
                cr_ids['partner_id'] = sale_obj.partner_id.id
                cr_ids['name'] = 'Shipping Charge for %s' % sale_line.name
                cr_ids_list.append(cr_ids.copy())

        else:
            vals['journal_id'] = False
        vals['partner_id'] = sale_obj.partner_id.id
        #vals['date'] = sale_obj.date_order
        vals['rel_sale_order_id'] = ids[0]
        vals['name'] = 'Auto generated Sales Receipt'
        vals['type'] = 'sale'
        vals['currency_id'] = journal_obj.company_id.currency_id.id
        vals['line_cr_ids'] = [(0, 0, cr_ids) for cr_ids in cr_ids_list]
#        vals['narration'] = voucher_obj.narration
        vals['pay_now'] = 'pay_now'
        vals['account_id'] = journal_obj.default_debit_account_id.id  
#        vals['reference'] = voucher_obj.reference
#        vals['tax_id'] = voucher_obj.tax_id.id
        vals['amount'] = sale_obj.amount_total
        vals['company_id'] = journal_obj.company_id.id
        vals['origin'] = sale_obj.name

        voucher_id = self.pool.get('account.voucher').create(cr, uid, vals, context)

        return voucher_id

    def action_wait(self, cr, uid, ids, context=None):
        ret = super(sale_order, self).action_wait(cr, uid, ids, context=context)
        for o in self.browse(cr, uid, ids, context=context):
            if (o.order_policy == 'credit_card'):
                #self.create_sales_reciept(cr, uid, [o.id])
                invoice_id = self.action_invoice_create(cr, uid, [o.id], context=context)
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
                self.pool.get('account.invoice').write(cr, uid, invoice_id, {'credit_card': True}, context=context)
        return ret
    
    def action_cancel(self, cr, uid, ids, context=None):
        for sale in self.browse(cr, uid, ids, context=context):
            for picking in sale.picking_ids:
                if sale.order_policy == 'credit_card' and picking.state not in ('done', 'cancel'):
                    self.pool.get('stock.picking').action_cancel(cr, uid, [picking.id], {})
            for inv in sale.invoice_ids:
                if sale.order_policy == 'credit_card':
                    self.pool.get('account.invoice').action_cancel(cr, uid, [inv.id], {})
        return super(sale_order, self).action_cancel(cr, uid, ids, context)
    
sale_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
