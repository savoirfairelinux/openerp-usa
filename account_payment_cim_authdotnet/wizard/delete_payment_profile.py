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
from xml.dom.minidom import Document
import xml2dic
from tools.translate import _
import httplib

class delete_payment_profile(osv.TransientModel):
    _name = 'delete.payment.profile'
    _description = 'Delete Payment Profile'

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

    def deleteCustomerPaymentProfile(self, dic):
        KEYS = dic.keys()
        doc1 = Document()
        url_path = dic.get('url_extension', False)
        url = dic.get('url', False)
        xsd = dic.get('xsd', False)

        deleteCustomerPaymentProfileRequest = doc1.createElement("deleteCustomerPaymentProfileRequest")
        deleteCustomerPaymentProfileRequest.setAttribute("xmlns", xsd)
        doc1.appendChild(deleteCustomerPaymentProfileRequest)

        merchantAuthentication = doc1.createElement("merchantAuthentication")
        deleteCustomerPaymentProfileRequest.appendChild(merchantAuthentication)

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

        if 'customerProfileId' in KEYS:
            customerProfileId = doc1.createElement("customerProfileId")
            deleteCustomerPaymentProfileRequest.appendChild(customerProfileId)
            ptext = doc1.createTextNode(self._clean_string(dic['customerProfileId']))
            customerProfileId.appendChild(ptext)

        if 'customerPaymentProfileId' in KEYS:
            customerPaymentProfileId = doc1.createElement("customerPaymentProfileId")
            deleteCustomerPaymentProfileRequest.appendChild(customerPaymentProfileId)
            ptext = doc1.createTextNode(self._clean_string(dic['customerPaymentProfileId']))
            customerPaymentProfileId.appendChild(ptext)

        Request_string = doc1.toxml(encoding="utf-8")
        delete_CustomerPaymentProfile_response_xml = self.request_to_server(Request_string, url, url_path)
        delete_CustomerPaymentProfile_response_dictionary = xml2dic.main(delete_CustomerPaymentProfile_response_xml)
        parent_resultCode = self.search_dic(delete_CustomerPaymentProfile_response_dictionary, 'resultCode')
        if parent_resultCode:
            if  parent_resultCode['resultCode'] == 'Ok':
                return True
            ret = {}
            Error_Code_dic = self.search_dic(delete_CustomerPaymentProfile_response_dictionary, 'code')
            if Error_Code_dic.get('code'):
                ret['Error_Code'] = Error_Code_dic['code']
            Error_message_dic = self.search_dic(delete_CustomerPaymentProfile_response_dictionary, 'text')
            if  Error_message_dic.get('text'):
                ret['Error_Message'] = Error_message_dic['text']
            return ret
        return

    def del_pay_profile(self, cr, uid, ids, context=None):
        Param_Dic = {}
        parent_model = context.get('active_model')
        parent_id = context.get('active_id')
        if parent_model == 'res.partner':
            partner = self.pool.get(parent_model).browse(cr, uid, parent_id)
        else:
            parent_model_obj = self.pool.get(parent_model).browse(cr, uid, parent_id)
            partner = parent_model_obj.address_id.partner_id

        data = self.pool.get('delete.payment.profile').browse(cr, uid, ids[0])

        Trans_key = partner.company_id.auth_config_id.transaction_key
        Login_id = partner.company_id.auth_config_id.login_id
        url_extension = partner.company_id.auth_config_id.url_extension
        xsd = partner.company_id.auth_config_id.xsd_link
        prof_id = partner.payment_profile_id.name
        customerPaymentProfileId = data.payment_profile_id.name
        if partner.company_id.auth_config_id.test_mode:
            url = partner.company_id.auth_config_id.url_test
        else:
            url = partner.company_id.auth_config_id.url

        if Trans_key and Login_id:
            self._setparameter(Param_Dic, 'api_login_id', Login_id)
            self._setparameter(Param_Dic, 'transaction_key', Trans_key)

            if url:
                self._setparameter(Param_Dic, 'url', url)
                self._setparameter(Param_Dic, 'url_extension', url_extension)
            if xsd:
                self._setparameter(Param_Dic, 'xsd', xsd)

            self._setparameter(Param_Dic, 'customerProfileId', prof_id)
            self._setparameter(Param_Dic, 'customerPaymentProfileId', customerPaymentProfileId)

            Customer_Payment_Profile_ID = self.deleteCustomerPaymentProfile(Param_Dic)
            self.pool.get('cust.payment.profile').unlink(cr, uid, data.payment_profile_id.id)
            if not Customer_Payment_Profile_ID or type(Customer_Payment_Profile_ID) == type({}):
                raise osv.except_osv(_('Transaction Error'), _('Error code : ' + Customer_Payment_Profile_ID.get('Error_Message') or '' + '\nError Message :' + Customer_Payment_Profile_ID.get('Error_Message') or ''))

            return{}

    def _get_profile_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('active_model') == 'cust.payment.profile':
            return context.get('active_id')
        return None

    _columns = {
        'payment_profile_id':fields.many2one('cust.payment.profile', 'Payment Profile', required=True),
        }
    _defaults = {
        'payment_profile_id':_get_profile_id
    }
