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

from openerp.osv import fields, osv
import httplib
from xml.dom.minidom import Document
import xml2dic
import time
from tools.translate import _

class make_transaction(osv.TransientModel):
    _name = 'make.transaction'
    _description = 'Make Transaction'

    def onchange_trans_type(self, cr, uid, ids, trans_type, context=None):
        res = {}
        if trans_type in ['AuthOnly', 'AuthCapture', 'CaptureOnly']:
            res['value'] = {'invisible': True}
        else:
            res['value'] = {'invisible': False}
        return res

    def _get_partner(self, cr, uid, context=None):
        return context and context.get('partner_id') or False

    def _get_profile(self, cr, uid, context=None):
        return context and context.get('payment_profile_id') or False

    _columns = {
    'amount':fields.integer('Amount', size=32, required=True),
    'trans_type': fields.selection([('AuthOnly', 'Authorization Only'),
                                     ('AuthCapture', 'Authorization And Capture'),
                                     ('CaptureOnly', 'Capture Only'),
                                     ('PriorAuthCapture', 'Prior Authorization Capture'),
                                     ('Refund', 'Credit/Refund'),
                                     ('Void', 'Void'), ], 'Type', size=32, required=True),
    'partner_id':fields.many2one('res.partner', 'Customer', required=True),
    'payment_profile_id':fields.many2one('cust.payment.profile', 'Payment Profile', required=True),
    'trans_id':fields.many2one('transaction.history', 'Transaction ID'),
    'invisible':fields.boolean('invisible'),
    }

    _defaults = {
    'partner_id': _get_partner,
    'payment_profile_id':_get_profile
    }

    def createCustomerProfileTransactionRequest(self, dic):

            ''' Creates the xml for TransactionRequest and returns the transaction id '''

            profile_dictionary = dic
            KEYS = dic.keys()

            doc1 = Document()
            url_path = dic.get('url_extension', False)
            url = dic.get('url', False)
            xsd = dic.get('xsd', False)
            trans_type_list = ['AuthOnly', 'AuthCapture', 'CaptureOnly', 'PriorAuthCapture', 'Refund', ]

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
                if profile_dictionary.get('trans_type') in trans_type_list:
                    transaction_type_tagname = 'profileTrans' + profile_dictionary.get('trans_type')
                    transaction_type = doc1.createElement(transaction_type_tagname)
                    transaction.appendChild(transaction_type)

                    if 'amount' in KEYS :
                        amount = doc1.createElement('amount')
                        transaction_type.appendChild(amount)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('amount')))
                        amount.appendChild(ptext)

                    if 'tax_amount' in KEYS :
                        tax = doc1.createElement('tax')
                        transaction_type.appendChild(tax)

                        tax_amount = doc1.createElement('amount')
                        tax.appendChild(tax_amount)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('tax_amount')))
                        tax_amount.appendChild(ptext)

                        tax_name = doc1.createElement('name')
                        tax.appendChild(tax_name)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('tax_name')))
                        tax_name.appendChild(ptext)

                        tax_description = doc1.createElement('description')
                        tax.appendChild(tax_description)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('tax_description')))
                        tax_description.appendChild(ptext)

                    if 'shipping_amount' in KEYS :
                        shipping = doc1.createElement('shipping')
                        transaction_type.appendChild(shipping)

                        shipping_amount = doc1.createElement('amount')
                        tax.appendChild(shipping_amount)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('shipping_amount')))
                        shipping_amount.appendChild(ptext)

                        shipping_name = doc1.createElement('name')
                        tax.appendChild(shipping_name)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('shipping_name')))
                        shipping_name.appendChild(ptext)

                        shipping_description = doc1.createElement('description')
                        tax.appendChild(shipping_description)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('shipping_description')))
                        shipping_description.appendChild(ptext)

                    if 'duty_amount' in KEYS :
                        duty = doc1.createElement('duty')
                        transaction_type.appendChild(duty)

                        duty_amount = doc1.createElement('amount')
                        tax.appendChild(duty_amount)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('duty_amount')))
                        duty_amount.appendChild(ptext)

                        duty_name = doc1.createElement('name')
                        tax.appendChild(duty_name)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('duty_name')))
                        duty_name.appendChild(ptext)

                        duty_description = doc1.createElement('description')
                        tax.appendChild(duty_description)
                        ptext = doc1.createTextNode(self._clean_string(dic.get('duty_description')))
                        duty_description.appendChild(ptext)

                    if 'items'in KEYS and len(profile_dictionary['items']) > 0:
                        for i in range(0, len(profile_dictionary['items'])):
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

                    if transaction_type_tagname == 'profileTransCaptureOnly':
                        approvalCode = doc1.createElement('approvalCode')
                        transaction_type.appendChild(approvalCode)
                        ptext = doc1.createTextNode('000000')
                        approvalCode.appendChild(ptext)

                    if transaction_type_tagname == 'profileTransPriorAuthCapture' or transaction_type_tagname == 'profileTransRefund'  :
                        transId = doc1.createElement('transId')
                        transaction_type.appendChild(transId)
                        if 'transId' in KEYS:
                            ptext = doc1.createTextNode(self._clean_string(profile_dictionary['transId']))
                            transId.appendChild(ptext)

                    if  transaction_type_tagname == 'profileTransRefund':
                        if 'creditCardNumberMasked' in KEYS:
                            creditCardNumberMasked = doc1.createElement('creditCardNumberMasked')
                            transaction_type.appendChild(creditCardNumberMasked)
                            ptext = doc1.createTextNode(self._clean_string(profile_dictionary['creditCardNumberMasked']))
                            creditCardNumberMasked.appendChild(ptext)

                elif  profile_dictionary.get('trans_type') == 'Void':
                    transaction_type_tagname = 'profileTrans' + profile_dictionary.get('trans_type')
                    transaction_type = doc1.createElement(transaction_type_tagname)
                    transaction.appendChild(transaction_type)

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

                    if 'transId' in KEYS:
                        transId = doc1.createElement('transId')
                        transaction_type.appendChild(transId)
                        ptext = doc1.createTextNode(self._clean_string(profile_dictionary['transId']))
                        transId.appendChild(ptext)

                if 'extraOptions' in KEYS:
                    extraOptions = doc1.createElement("extraOptions")
                    createCustomerProfileTransactionRequest.appendChild(extraOptions)

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
                    return li[6]
                ret = {}
                Error_Code_dic = self.search_dic(create_transaction_response_dictionary, 'code')
                if Error_Code_dic.get('code'):
                    ret['Error_Code'] = Error_Code_dic['code']
                Error_message_dic = self.search_dic(create_transaction_response_dictionary, 'text')
                if  Error_message_dic.get('text'):
                    ret['Error_Message'] = Error_message_dic['text']
                return ret

    def request_to_server(self, Request_string, url, url_path):
            ''' Sends a POST request to url and returns the response from the server'''

            conn = httplib.HTTPSConnection(url)
            conn.putrequest('POST', url_path)
            conn.putheader('content-type', 'text/xml')
            conn.putheader('content-length', len(Request_string))
            conn.endheaders()
            conn.send(Request_string)
            response = conn.getresponse()
            create_CustomerProfile_response_xml = response.read()
            return create_CustomerProfile_response_xml

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

    def _clean_string(self, text):
        lis = ['\t', '\n']
        if type(text) != type(''):
            text = str(text)
        for t in lis:
            text = text.replace(t, '')
        return text

    def _setparameter(self, dic, key, value):
        ''' Used to input parameters to corresponding dictionary'''
        if key == None or value == None :
            return
        if type(value) == type(''):
            dic[key] = value.strip()
        else:
            dic[key] = value

    def do_cc_transaction(self, cr, uid, ids, context=None):
        Param_Dic = {}
        data = self.browse(cr, uid, ids[0])

        customer = data.partner_id
        amount = data.amount
        trans_type = data.trans_type
        trans_id = data.trans_id.trans_id
        Customer_Profile_ID = customer.payment_profile_id.name
        customerPaymentProfileId = data.payment_profile_id.name
        Trans_key = customer.company_id.auth_config_id.transaction_key
        Login_id = customer.company_id.auth_config_id.login_id
        url_extension = customer.company_id.auth_config_id.url_extension
        xsd = customer.company_id.auth_config_id.xsd_link
        if customer.company_id.auth_config_id.test_mode:
            url = customer.company_id.auth_config_id.url_test
        else:
            url = customer.company_id.auth_config_id.url

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
            self._setparameter(Param_Dic, 'amount', amount)
            self._setparameter(Param_Dic, 'trans_type', trans_type)
#            self._setparameter(Param_Dic,'description',description)

            if trans_type in ['Void', 'PriorAuthCapture', 'Refund', ]:
                 self._setparameter(Param_Dic, 'transId', trans_id)
            Transaction_ID = self.createCustomerProfileTransactionRequest(Param_Dic)
            if Transaction_ID and type(Transaction_ID) == type('') :
                pay_profile_ids = self.pool.get('cust.payment.profile').search(cr, uid, [('name', '=', customerPaymentProfileId)])
                for pay_id in pay_profile_ids:
                    trans_history_id = self.pool.get('transaction.history').create(cr, uid, {'trans_id':Transaction_ID,
                                                                                         'payment_profile_id':pay_id,
                                                                                         'amount':amount,
                                                                                         'trans_type':trans_type,
                                                                                         'transaction_date':time.strftime('%m/%d/%Y %H:%M:%S')
                                                                                         })
            raise osv.except_osv(_('Transaction Error'), _('Error code : ' + Transaction_ID.get('Error_Message') or '' + '\nError Message :' + Transaction_ID.get('Error_Message') or ''))

        return {}
