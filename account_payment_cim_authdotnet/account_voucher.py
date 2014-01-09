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
from openerp import netsvc
import httplib
from xml.dom.minidom import Document
import xml2dic
import time
from tools.translate import _


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

class auth_net_cc_api(osv.Model):
    _inherit = "auth.net.cc.api"
    '''
        Class to do credit card transaction
    '''
    def _setparameter(self, dic, key, value):
        ''' Used to input parameters to corresponding dictionary'''
        if key == None or value == None :
            return
        if type(value) == type(''):
            dic[key] = value.strip()
        else:
            dic[key] = value

    def createCustomerProfileTransactionRequest(self, dic):

            ''' Creates the xml for TransactionRequest and returns the transaction id '''

            profile_dictionary = dic
            KEYS = dic.keys()
            doc1 = Document()
            url_path = dic.get('url_extension', False)
            url = dic.get('url', False)
            xsd = dic.get('xsd', False)
            trans_type_list = ['AuthOnly', 'PriorAuthCapture', 'Refund']

            createCustomerProfileTransactionRequest = doc1.createElement("createCustomerProfileTransactionRequest")
            createCustomerProfileTransactionRequest.setAttribute("xmlns", xsd)
            doc1.appendChild(createCustomerProfileTransactionRequest)

            merchantAuthentication = doc1.createElement("merchantAuthentication")
            createCustomerProfileTransactionRequest.appendChild(merchantAuthentication)

            name = doc1.createElement("name")
            merchantAuthentication.appendChild(name)

            transactionKey = doc1.createElement("transactionKey")
            merchantAuthentication.appendChild(transactionKey)

            ##Create the Request for creating the customer profile
            if 'api_login_id' in KEYS and 'transaction_key' in KEYS:

                ptext1 = doc1.createTextNode(self._clean_string(dic['api_login_id']))
                name.appendChild(ptext1)

                ptext = doc1.createTextNode(self._clean_string(self._clean_string(dic['transaction_key'])))
                transactionKey.appendChild(ptext)

            transaction = doc1.createElement("transaction")
            createCustomerProfileTransactionRequest.appendChild(transaction)
            if 'trans_type' in KEYS :
                if profile_dictionary.get('trans_type', False) in trans_type_list:
                    transaction_type_tagname = 'profileTrans' + profile_dictionary.get('trans_type', False)
                    transaction_type = doc1.createElement(transaction_type_tagname)
                    transaction.appendChild(transaction_type)

                    if 'amount' in KEYS :
                        amount = doc1.createElement('amount')
                        transaction_type.appendChild(amount)
                        ptext = doc1.createTextNode(self._clean_string(dic['amount']))
                        amount.appendChild(ptext)

                    if 'tax_amount' in KEYS :
                        tax = doc1.createElement('tax')
                        transaction_type.appendChild(tax)

                        tax_amount = doc1.createElement('amount')
                        tax.appendChild(tax_amount)
                        ptext = doc1.createTextNode(self._clean_string(dic['tax_amount']))
                        tax_amount.appendChild(ptext)

                        tax_name = doc1.createElement('name')
                        tax.appendChild(tax_name)
                        ptext = doc1.createTextNode(self._clean_string(dic['tax_name']))
                        tax_name.appendChild(ptext)

                        tax_description = doc1.createElement('description')
                        tax.appendChild(tax_description)
                        ptext = doc1.createTextNode(self._clean_string(dic['tax_description']))
                        tax_description.appendChild(ptext)

                    if 'shipping_amount' in KEYS :
                        shipping = doc1.createElement('shipping')
                        transaction_type.appendChild(shipping)

                        shipping_amount = doc1.createElement('amount')
                        tax.appendChild(shipping_amount)
                        ptext = doc1.createTextNode(self._clean_string(dic['shipping_amount']))
                        shipping_amount.appendChild(ptext)

                        shipping_name = doc1.createElement('name')
                        tax.appendChild(shipping_name)
                        ptext = doc1.createTextNode(self._clean_string(dic['shipping_name']))
                        shipping_name.appendChild(ptext)

                        shipping_description = doc1.createElement('description')
                        tax.appendChild(shipping_description)
                        ptext = doc1.createTextNode(self._clean_string(dic['shipping_description']))
                        shipping_description.appendChild(ptext)

                    if 'duty_amount' in KEYS :
                        duty = doc1.createElement('duty')
                        transaction_type.appendChild(duty)

                        duty_amount = doc1.createElement('amount')
                        tax.appendChild(duty_amount)
                        ptext = doc1.createTextNode(self._clean_string(dic['duty_amount']))
                        duty_amount.appendChild(ptext)

                        duty_name = doc1.createElement('name')
                        tax.appendChild(duty_name)
                        ptext = doc1.createTextNode(self._clean_string(dic['duty_name']))
                        duty_name.appendChild(ptext)

                        duty_description = doc1.createElement('description')
                        tax.appendChild(duty_description)
                        ptext = doc1.createTextNode(self._clean_string(dic['duty_description']))
                        duty_description.appendChild(ptext)

                    if 'items'in KEYS and len(profile_dictionary.get('items')) > 0:
                        for i in range(0, len(profile_dictionary.get('items'))):
                            lineItems = doc1.createElement('lineItems')
                            transaction_type.appendChild(lineItems)

                            if 'itemId' in  profile_dictionary['items'][i].keys():
                                itemId = doc1.createElement('itemId')
                                lineItems.appendChild(itemId)
                                ptext = doc1.createTextNode(self._clean_string(profile_dictionary['items'][0]['itemId']))
                                itemId.appendChild(ptext)

                            if 'name' in  profile_dictionary['items'][i].keys():
                                name = doc1.createElement('name')
                                lineItems.appendChild(name)
                                ptext = doc1.createTextNode(self._clean_string(profile_dictionary['items'][0]['name']))
                                name.appendChild(ptext)

                            if 'description' in  profile_dictionary['items'][i].keys():
                                description = doc1.createElement('description')
                                lineItems.appendChild(description)
                                ptext = doc1.createTextNode(self._clean_string(profile_dictionary['items'][0]['description']))
                                description.appendChild(ptext)

                            if 'quantity' in  profile_dictionary['items'][i].keys():
                                quantity = doc1.createElement('quantity')
                                lineItems.appendChild(quantity)
                                ptext = doc1.createTextNode(self._clean_string(profile_dictionary['items'][0]['quantity']))
                                quantity.appendChild(ptext)

                            if 'unitPrice' in  profile_dictionary['items'][i].keys():
                                unitPrice = doc1.createElement('unitPrice')
                                lineItems.appendChild(unitPrice)
                                ptext = doc1.createTextNode(self._clean_string(profile_dictionary['items'][0]['unitPrice']))
                                unitPrice.appendChild(ptext)

                            if 'taxable' in  profile_dictionary['items'][i].keys():
                                taxable = doc1.createElement('taxable')
                                lineItems.appendChild(taxable)
                                ptext = doc1.createTextNode(self._clean_string(profile_dictionary['items'][0]['taxable']))
                                taxable.appendChild(ptext)

                    if 'customerProfileId' in KEYS:
                        customerProfileId = doc1.createElement('customerProfileId')
                        transaction_type.appendChild(customerProfileId)
                        ptext = doc1.createTextNode(self._clean_string(profile_dictionary['customerProfileId']))
                        customerProfileId.appendChild(ptext)

                    if 'customerPaymentProfileId' in KEYS:
                        customerProfileId = doc1.createElement('customerPaymentProfileId')
                        transaction_type.appendChild(customerProfileId)
                        ptext = doc1.createTextNode(self._clean_string(profile_dictionary['customerPaymentProfileId']))
                        customerProfileId.appendChild(ptext)

                    if 'customerShippingAddressId' in KEYS:
                        customerShippingAddressId = doc1.createElement('customerShippingAddressId')
                        transaction_type.appendChild(customerShippingAddressId)
                        ptext = doc1.createTextNode(self._clean_string(profile_dictionary['customerShippingAddressId']))
                        customerShippingAddressId.appendChild(ptext)

                    if  transaction_type_tagname in ['profileTransRefund', 'profileTransPriorAuthCapture']:
                        if 'transId' in KEYS:
                            transId = doc1.createElement('transId')
                            transaction_type.appendChild(transId)
                            ptext = doc1.createTextNode(self._clean_string(profile_dictionary['transId']))
                            transId.appendChild(ptext)
                        if 'creditCardNumberMasked' in KEYS:
                            creditCardNumberMasked = doc1.createElement('creditCardNumberMasked')
                            transaction_type.appendChild(creditCardNumberMasked)
                            ptext = doc1.createTextNode(self._clean_string(profile_dictionary['creditCardNumberMasked']))
                            creditCardNumberMasked.appendChild(ptext)

            Request_string = xml = doc1.toxml(encoding="utf-8")
            create_transaction_response_xml = self.request_to_server(Request_string, url, url_path)
            create_transaction_response_dictionary = xml2dic.main(create_transaction_response_xml)
            parent_resultCode = self.search_dic(create_transaction_response_dictionary, 'resultCode')
            if parent_resultCode:
                if  parent_resultCode['resultCode'] == 'Ok':
                    parent_directResponse = self.search_dic(create_transaction_response_dictionary, 'directResponse')
                    li = parent_directResponse['directResponse'].split(',')
                    li[6]##Transaction ID
                    li[4]##Authorization code
                    return li
                ret = {}
                Error_Code_dic = self.search_dic(create_transaction_response_dictionary, 'code')
                if Error_Code_dic.get('code'):
                    ret['Error_Code'] = Error_Code_dic['code']
                Error_message_dic = self.search_dic(create_transaction_response_dictionary, 'text')
                if  Error_message_dic.get('text'):
                    ret['Error_Message'] = Error_message_dic['text']
                return ret

    def getCustomerPaymentProfileRequest(self, dic):
        profile_dictionary = dic
        KEYS = dic.keys()
        doc1 = Document()
        url_path = dic.get('url_extension')
        url = dic.get('url')
        xsd = dic.get('xsd')

        getCustomerPaymentProfileRequest = doc1.createElement("getCustomerPaymentProfileRequest")
        getCustomerPaymentProfileRequest.setAttribute("xmlns", "AnetApi/xml/v1/schema/AnetApiSchema.xsd")
        doc1.appendChild(getCustomerPaymentProfileRequest)

        merchantAuthentication = doc1.createElement("merchantAuthentication")
        getCustomerPaymentProfileRequest.appendChild(merchantAuthentication)

        name = doc1.createElement("name")
        merchantAuthentication.appendChild(name)

        transactionKey = doc1.createElement("transactionKey")
        merchantAuthentication.appendChild(transactionKey)
        if 'api_login_id' in KEYS and 'transaction_key' in KEYS:
            ptext1 = doc1.createTextNode(self._clean_string(dic['api_login_id']))
            name.appendChild(ptext1)

            ptext = doc1.createTextNode(self._clean_string(self._clean_string(dic['transaction_key'])))
            transactionKey.appendChild(ptext)

        if 'customerProfileId' in KEYS:
            customerProfileId = doc1.createElement("customerProfileId")
            getCustomerPaymentProfileRequest.appendChild(customerProfileId)
            ptext = doc1.createTextNode(self._clean_string(profile_dictionary['customerProfileId']))
            customerProfileId.appendChild(ptext)

        if 'customerPaymentProfileId' in KEYS:
            customerPaymentProfileId = doc1.createElement("customerPaymentProfileId")
            getCustomerPaymentProfileRequest.appendChild(customerPaymentProfileId)
            ptext = doc1.createTextNode(self._clean_string(profile_dictionary['customerPaymentProfileId']))
            customerPaymentProfileId.appendChild(ptext)

        Request_string = xml = doc1.toxml(encoding="utf-8")

        get_profile_response_xml = self.request_to_server(Request_string, url, url_path)
        get_profile_response_dictionary = xml2dic.main(get_profile_response_xml)

        parent_resultCode = self.search_dic(get_profile_response_dictionary, 'resultCode')

        if parent_resultCode:
                if  parent_resultCode['resultCode'] == 'Ok':
                    parent_directResponse = self.search_dic(get_profile_response_dictionary, 'cardNumber')
                    cardNumber = parent_directResponse['cardNumber']
        return cardNumber

    def validate_sales_reciept(self, cr, uid, ids, context={}):
        vouchr_obj = self.pool.get('account.voucher')
        if type(ids) == type([]):
            voucher_objs = vouchr_obj.browse(cr, uid, ids, context=context)
        else:
            voucher_objs = vouchr_obj.browse(cr, uid, [ids], context=context)
        for voucher_obj in voucher_objs:
            rel_sale_order_id = voucher_obj.rel_sale_order_id and voucher_obj.rel_sale_order_id.id
            if rel_sale_order_id:
                sale_reciepts_ids = vouchr_obj.search(cr, uid, [('type', '=', 'sale'), ('rel_sale_order_id', '=', rel_sale_order_id), ('state', 'in', ['draft'])])

            if sale_reciepts_ids:
                vouchr_obj.action_move_line_create(cr, uid, sale_reciepts_ids, context=context)
            else:
                sale_reciepts_id = self.pool.get('sale.order').create_sales_reciept(cr, uid, [rel_sale_order_id], context=context)
                vouchr_obj.action_move_line_create(cr, uid, [sale_reciepts_id], context=context)
        return True

    def _clean_string(self, text):
        lis = ['\t', '\n']
        if type(text) != type(''):
            text = str(text)
        for t in lis:
            text = text.replace(t, '')
        return text

    def request_to_server(self, Request_string, url, url_path):
        ''' Sends a POST request to url and returns the response from the server'''

        conn = httplib.HTTPSConnection(url)
        conn.putrequest('POST', url_path)
        conn.putheader('content-type', 'text/xml')
        conn.putheader('content-length', len(Request_string))
        conn.endheaders()
        conn.send(Request_string)
        response = conn.getresponse()
        get_CustomerProfile_response_xml = response.read()
        return get_CustomerProfile_response_xml

    def search_dic(self, dic, key):
        ''' Returns the parent dictionary containing key None on Faliure'''
        if key in dic.keys():
            return dic
        for k in dic.keys():
            if type(dic[k]) == type([]):
                for i in dic[k]:
                    if type(i) == type({}):
                        ret = self.search_dic(i, key)
                        if ret and key in ret.keys():
                           return ret
        return None

    def do_this_transaction(self, cr, uid, ids, refund=False, context=None):
        '''
        Do credit card transaction
        '''
        voucher_obj = self.pool.get('account.voucher')
        vou_line_obj = self.pool.get('account.voucher.line')
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        sale_obj = self.pool.get('sale.order')
        wf_service = netsvc.LocalService('workflow')
        if type([]) == type(ids):
            acc_voucher_obj = voucher_obj.browse(cr, uid, ids[0], context={'cc_no':'no_mask'})
        else:
            acc_voucher_obj = voucher_obj.browse(cr, uid, ids, context={'cc_no':'no_mask'})
        if not acc_voucher_obj.payment_profile_id:
            raise osv.except_osv(_('No Payment Profile!'), _(" Select Payment Profile."))
        ret = False
        company = acc_voucher_obj.partner_id and acc_voucher_obj.partner_id.company_id
        customer = acc_voucher_obj.partner_id
        user = self.pool.get('res.users').browse(cr, uid, uid)
        amount = acc_voucher_obj.cc_order_amt
        if amount <= 0.00:
            raise osv.except_osv(_('No Amount!'), _(" Enter a Positive Amount"))
        trans_type = acc_voucher_obj.trans_type or 'AuthOnly'
        trans_id = acc_voucher_obj.cc_trans_id or False
        if refund:
            trans_type = 'Refund'
            amount = acc_voucher_obj.cc_refund_amt
            if not trans_id:
                raise osv.except_osv(_('No Transaction ID!'), _(" Unable to find transaction id for refund."))
#             if not acc_voucher_obj.journal_id.cc_allow_refunds:
#                 raise osv.except_osv(_('Unable to do Refund!'), _("Please check \"Allow Credit Card Refunds\" on journal to do refund."))
        if company and company.auth_config_id:
            Login_id = company.auth_config_id.login_id
            Trans_key = company.auth_config_id.transaction_key
            url_extension = company.auth_config_id.url_extension
            xsd = company.auth_config_id.xsd_link
            if company.auth_config_id.test_mode == True:
                url = company.auth_config_id.url_test
            else:
                url = company.auth_config_id.url

        if acc_voucher_obj.payment_profile_id:
            customerPaymentProfileId = acc_voucher_obj.payment_profile_id.name
            Customer_Profile_ID = acc_voucher_obj.payment_profile_id.cust_profile_id.name
            CustomerShippingAddressRequest_ID = acc_voucher_obj.payment_profile_id.cust_profile_id.shipping_address_id

        Param_Dic = {}
        if Trans_key and Login_id:
            self._setparameter(Param_Dic, 'api_login_id', Login_id)
            self._setparameter(Param_Dic, 'transaction_key', Trans_key)

            if url:
                self._setparameter(Param_Dic, 'url', url)
                self._setparameter(Param_Dic, 'url_extension', url_extension)
            if xsd:
                self._setparameter(Param_Dic, 'xsd', xsd)

            self._setparameter(Param_Dic, 'customerProfileId', Customer_Profile_ID)
            self._setparameter(Param_Dic, 'customerPaymentProfileId', customerPaymentProfileId)
            if CustomerShippingAddressRequest_ID:
                self._setparameter(Param_Dic, 'customerShippingAddressId', CustomerShippingAddressRequest_ID)
            self._setparameter(Param_Dic, 'amount', amount)
            self._setparameter(Param_Dic, 'trans_type', trans_type)

            if trans_type in ['Refund', 'PriorAuthCapture']:
                self._setparameter(Param_Dic, 'transId', trans_id)
#                 creditCardNumberMasked = self.getCustomerPaymentProfileRequest(Param_Dic)
#                 self._setparameter(Param_Dic,'creditCardNumberMasked',creditCardNumberMasked)
        Transaction = self.createCustomerProfileTransactionRequest(Param_Dic)

        if Transaction and type(Transaction) == type([]) :
                Transaction_ID = Transaction[6]
                pay_profile_ids = self.pool.get('cust.payment.profile').search(cr, uid, [('name', '=', customerPaymentProfileId)])
                for pay_id in pay_profile_ids:
                    trans_history_id = self.pool.get('transaction.history').create(cr, uid, {'trans_id':Transaction_ID,
                                                                                         'payment_profile_id':pay_id,
                                                                                         'amount':amount,
                                                                                         'trans_type':trans_type,
                                                                                         'transaction_date':time.strftime('%m/%d/%Y %H:%M:%S'),
                                                                                         })

                if Transaction[0] == '1' and acc_voucher_obj.rel_sale_order_id and acc_voucher_obj.rel_sale_order_id.id:
                    if acc_voucher_obj.rel_sale_order_id.state == 'done':
                        so_vals = {'cc_pre_auth':True, 'rel_account_voucher_id':acc_voucher_obj.id}
                    else:
                        so_vals = {'state':'cc_auth', 'cc_pre_auth':True, 'rel_account_voucher_id':acc_voucher_obj.id}
                    self.pool.get('sale.order').write(cr, uid, [acc_voucher_obj.rel_sale_order_id.id], so_vals)

                ret_dic = {}
                
                if trans_type == 'AuthOnly':
                    status = 'Authorization: ' + str(Transaction[3])
                    ret_dic.update({
                         'cc_status' : status,
                         'cc_auth_code':Transaction[4],
                         'cc_trans_id':Transaction[6]
                         })
                    voucher_obj.write(cr, uid, ids[0], ret_dic)
                    pay_profile_ids = self.pool.get('cust.payment.profile').search(cr, uid, [('name', '=', customerPaymentProfileId)])
                    for pay_id in pay_profile_ids:
                        vals = {'trans_id':Transaction[6],
                                 'payment_profile_id':pay_id,
                                 'amount':amount,
                                 'status':status,
                                 'trans_type':trans_type,
                                 'transaction_date':time.strftime('%m/%d/%Y %H:%M:%S'),
                                 'voucher_id':acc_voucher_obj.id
                        }
                        self.pool.get('transaction.details').create(cr, uid, vals)
                if trans_type == 'PriorAuthCapture':
                    status = 'Prior Authorization and Capture: ' + str(Transaction[3])
                    ret_dic['amount'] = acc_voucher_obj.cc_order_amt
                    ret_dic['cc_status'] = status
                    ret_dic['cc_trans_id'] = Transaction[6]
                    ret_dic['cc_transaction'] = True
                    ret_dic['is_charged'] = True
                    voucher_obj.write(cr, uid, ids[0], ret_dic)
                    if Transaction[0] == '1':
                         '''
                             Validating sales reciept
                         '''
#                         self.validate_sales_reciept(cr, uid, ids, context=context)
                         '''
                             Posting payment voucher
                         '''
                         voucher_obj.action_move_line_create(cr, uid, ids, context)
                         pay_profile_ids = self.pool.get('cust.payment.profile').search(cr, uid, [('name', '=', customerPaymentProfileId)])
                         for pay_id in pay_profile_ids:
                             vals = {'trans_id':Transaction[6],
                                 'payment_profile_id':pay_id,
                                 'amount':amount,
                                 'status':status,
                                 'trans_type':trans_type,
                                 'transaction_date':time.strftime('%m/%d/%Y %H:%M:%S'),
                                 'voucher_id':acc_voucher_obj.id
                                 }
                             self.pool.get('transaction.details').create(cr, uid, vals)
                         ret = True

                if trans_type == 'Refund':
                    status = 'Refund: ' + str(Transaction[3])
                    ret_dic['cc_status'] = status
#                    voucher_obj.write(cr, uid, ids[0], ret_dic)
#                    journal_obj = self.pool.get('account.journal')
                    if Transaction[0] == '1':
                        pay_profile_ids = self.pool.get('cust.payment.profile').search(cr, uid, [('name', '=', customerPaymentProfileId)])
                        for pay_id in pay_profile_ids:
                            vals = {'trans_id':Transaction[6],
                                 'payment_profile_id':pay_id,
                                 'amount':amount,
                                 'status':status,
                                 'trans_type':trans_type,
                                 'transaction_date':time.strftime('%m/%d/%Y %H:%M:%S'),
                                 'voucher_id':acc_voucher_obj.id
                                 }
                            self.pool.get('transaction.details').create(cr, uid, vals)
                        ret_dic['cc_transaction'] = False
                        refund_journal_id = False
                        j_ids = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'sale_refund')], context=context)
                        if j_ids:
                            refund_journal_id = j_ids[0]
                        if refund_journal_id and context.get('cc_refund'):
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

#                        ret = True
#                        refund_journal_id = False
#                        if user.company_id.cc_refund_journal_id:
#                            refund_journal_id = user.company_id.cc_refund_journal_id.id
#                        else:
#                            j_ids = journal_obj.search(cr, uid, [('type', '=', 'sale_refund')], context=context)
#                            if j_ids:
#                                refund_journal_id = j_ids[0]
#                        account_id = False
#                        if refund_journal_id:
#                            default_debit_account_id = journal_obj.browse(cr, uid, refund_journal_id, context=context).default_debit_account_id.id
#
#                        vals1 = payment_profile_id{
#                            'name' :  'Refund : ' + (acc_voucher_obj.rel_sale_order_id and str(acc_voucher_obj.rel_sale_order_id.name) or ''),
#                            'account_id' :  default_debit_account_id,
#                            'partner_id' : acc_voucher_obj.partner_id.id,
#                            'amount'    : acc_voucher_obj.cc_order_amt,
#                            'currency_id' :  user.company_id.currency_id.id,
#                            'origin':acc_voucher_obj.rel_sale_order_id and acc_voucher_obj.rel_sale_order_id.name or ''
#                        }
#
#                        vals = voucher_obj.onchange_partner_id(cr, uid, [], acc_voucher_obj.partner_id.id, refund_journal_id , acc_voucher_obj.cc_order_amt , user.company_id.currency_id.id, 'sale', time.time())
#                        vals.update(vals1)
#
#                        vals['journal_id'] = refund_journal_id
#                        vals['type'] = 'sale'
#
#                        voucher_id = voucher_obj.create(cr, uid, vals, context=context)
#
#                        if acc_voucher_obj.cc_order_amt == acc_voucher_obj.rel_sale_order_id.amount_total and acc_voucher_obj.rel_sale_order_id.shipcharge:
#                            sale_obj.write(cr, uid, [acc_voucher_obj.rel_sale_order_id.id], {'cc_ship_refund':True}, context=context)
#                        refund_voucher = False
#
#                        if 'cc_refund' not in context:
#                            refund_voucher = True
#                            sales_receipt_ids = voucher_obj.search(cr, uid, [('rel_sale_order_id', '=', acc_voucher_obj.rel_sale_order_id.id), ('state', '=', 'posted'), ('type', '=', 'sale')], order="id desc", context=context)
#
#                            for receipt in voucher_obj.browse(cr, uid, sales_receipt_ids, context):
#
#                                for line in receipt.line_ids:
#
#                                    if line.amount:
#                                        vals = {
#                                                'voucher_id': voucher_id,
#                                                'name' : line.name,
#                                                'account_id' : line.account_id.id,
#                                                'partner_id' : line.partner_id.id,
#                                                'amount' : line.amount,
#                                                'type': line.type,
#                                            }
#                                        line_id = vou_line_obj.create(cr, uid, vals, context)
#                                break
#
#                        else:
#                            for line in context['cc_refund']:
#                                product = self.pool.get('product.product').browse(cr, uid, line['product_id'], context)
#
#                                vals = {
#                                        'voucher_id': voucher_id,
#                                        'name' : product.name,
#                                        'account_id' : product.product_tmpl_id.property_account_income.id,
#                                        'partner_id' : acc_voucher_obj.partner_id.id,
#                                        'amount'    :  product.list_price * line['qty'],
#                                        'type' : 'cr',
#                                        }
#                                line_id = vou_line_obj.create(cr, uid, vals, context)
#                            if context.get('cc_ship_refund'):
#                                vals = {
#                                        'voucher_id': voucher_id,
#                                        'name' : 'Shipping Charges of ' + acc_voucher_obj.rel_sale_order_id.name,
#                                        'account_id' : acc_voucher_obj.rel_sale_order_id.ship_method_id and acc_voucher_obj.rel_sale_order_id.ship_method_id.account_id.id or False,
#                                        'partner_id' : acc_voucher_obj.partner_id.id,
#                                        'amount'    : context['cc_ship_refund'],
#                                        'type' : 'cr',
#                                        }
#                                line_id = vou_line_obj.create(cr, uid, vals, context)
#                                sale_obj.write(cr, uid, [acc_voucher_obj.rel_sale_order_id.id], {'cc_ship_refund':True}, context=context)
#
#                            if not refund_voucher:
#                                wf_service = netsvc.LocalService('workflow')
#                                wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
                    else:
                        ret_dic['cc_transaction'] = True
                    voucher_obj.write(cr, uid, ids, ret_dic)

        else:
            raise osv.except_osv(_('Transaction Error'), _('Error code : ' + Transaction.get('Error_Message') or '' + '\nError Message :' + Transaction.get('Error_Message') or ''))
        return ret

class account_voucher(osv.Model):
    _inherit = 'account.voucher'

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
            'trans_type': 'AuthOnly'
        }
        default.update(vals)
        return super(account_voucher, self).copy(cr, uid, id, default=default, context=context)

    def check_transaction(self, cr, uid, ids, context=None):
        transaction_record = self.browse( cr, uid, ids, context)
        for record in transaction_record:
            if 'trans_type' in self._columns.keys():
                if record.trans_type == 'AuthOnly' and record.cc_auth_code:
                    raise osv.except_osv(_('Error'), _("Already Authorized!"))
                if record.trans_type == 'PriorAuthCapture' and not record.cc_auth_code:
                    raise osv.except_osv(_('Error'), _("Pre-Authorize the transaction first!"))
            else:
                if record.cc_p_authorize and record.cc_auth_code:
                 raise osv.except_osv(_('Error'), _("Already Authorized!"))
                if record.cc_charge and not record.cc_auth_code:
                 raise osv.except_osv(_('Error'), _("Pre-Authorize the transaction first!"))
        return True

    def cancel_cc(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, { 'cc_status':'This Transaction has been Cancelled',
                                       'cc_auth_code':'',
                                       'cc_trans_id':'', })

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None, sale_id=False):
        ret = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)
        payment_obj = self.pool.get('cust.payment.profile')
        payment_profile_id = None
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            cust_pay_profile_ids = payment_obj.search(cr, uid, [('cust_profile_id', '=', partner.payment_profile_id.id)], limit = 1)
            payment_profile_id = cust_pay_profile_ids and cust_pay_profile_ids[0] or False
            if ret.get('value'):
                ret.get('value')['payment_profile_id'] = payment_profile_id
        return ret

    _columns = {
        'payment_profile_id': fields.many2one('cust.payment.profile', 'Payment Profile'),
        'cc_order_date':fields.date('Order Date'),
        'cc_order_amt':fields.float('Order Amt'),
        'cc_comment':fields.char('Comment', size=128),
        'trans_type': fields.selection([('AuthOnly', 'Authorization Only'),
                                 ('PriorAuthCapture', 'Prior Authorization And Capture'),
                                 ('Refund', 'Credit/Refund'), ], 'Type', size=32),
#    'transaction_details':

    }

    _defaults = {
         'trans_type' : 'AuthOnly'
    }

class Stock_Picking(osv.osv):
    _inherit = 'stock.picking'

    def ddo_partial(self, cr, uid, ids, partial_datas, context=None):
        voucher_obj = self.pool.get('account.voucher')
        res = super(Stock_Picking, self).do_partial(cr, uid, ids, partial_datas, context=context)
        for pick in self.browse(cr, uid, ids, context=context):
            IN = OUT = False
            if pick.type == 'in':
                if pick.invoice_state == 'cc_refund' and pick.voucher_id:
                    if pick.state == 'assigned' and not pick.backorder_id.id:
                        continue
                IN = True

            if pick.type == 'out':
                rel_voucher = pick.sale_id and pick.sale_id.rel_account_voucher_id or False
                if not (pick.invoice_state == 'credit_card' and rel_voucher and pick.state == 'done'):
                    continue
                OUT = True

            if IN or OUT:
                amount = 0.00
                vch_lines = []
                Lines = pick.move_lines
                if pick.backorder_id.id and pick.state=='assigned':
                    Lines = pick.backorder_id.move_lines
                for move in Lines:
                    partial_data = partial_datas.get('move%s'%(move.id), {})
                    new_qty = partial_data.get('product_qty',0.0)
                    line = {}
                    line['product_id'] = move.product_id.id
                    line['qty'] = new_qty
                    line['price_unit'] = move.product_id.list_price
                    if pick.sale_id:
                        for sale_line in pick.sale_id.order_line:
                            if sale_line.product_id and sale_line.product_id.id == move.product_id.id:
                                 line['price_unit'] = sale_line.price_unit
                                 amount = amount + ((sale_line.price_subtotal / sale_line.product_uom_qty or 1) * new_qty)
                                 break
                    vch_lines.append(line)

                if OUT:
                    vals = {}
                    sale = pick.sale_id
                    if sale and sale.payment_method == 'cc_pre_auth' and not sale.invoiced:
                        rel_voucher = sale.rel_account_voucher_id or False
                        if rel_voucher and rel_voucher.state != 'posted' and rel_voucher.cc_auth_code:
                            vals_vouch = {'cc_order_amt': amount,'cc_p_authorize': False, 'cc_charge': True}
                            if 'trans_type' in rel_voucher._columns.keys():
                                vals_vouch.update({'trans_type': 'PriorAuthCapture'})
                            voucher_obj.write(cr, uid, [rel_voucher.id], vals_vouch, context=context)
                            voucher_obj.authorize(cr, uid, [rel_voucher.id], context=context)
                if IN:
                    context['cc_refund'] = vch_lines
                    voucher_obj.write(cr, uid, [pick.voucher_id.id], {'cc_refund_amt':amount}, context=context)
                    self.pool.get('auth.net.cc.api').do_this_transaction(cr, uid, [pick.voucher_id.id] , refund=True, context=context)
        return res

