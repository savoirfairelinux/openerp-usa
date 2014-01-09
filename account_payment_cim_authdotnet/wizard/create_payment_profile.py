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
import urllib2
from tools.translate import _

class create_payment_profile(osv.TransientModel):
    _name = 'create.payment.profile'
    _description = 'Create Payment Profile'

    def _get_partner(self, cr, uid, context=None):
        if context is None:
            context = {}
        part = False
        if context.get('active_model','') == 'res.partner':
            part = context.get('active_id', False)
        elif context.get('active_model','') == 'account.voucher':
            part = self.pool.get('account.voucher').browse(cr, uid,context.get('active_id')).partner_id.id
        return part
            

    _columns = {
        'cc_number':fields.char('Credit Card Number', size=32, required=True),
        'cc_ed_month':fields.char('Expiration Date MM', size=2, required=True),
        'cc_ed_year':fields.char('Expiration Date YYYY', size=4 , required=True),
        'cc_verify_code':fields.char('Card Code Verification', size=3),
        'partner_id':fields.many2one('res.partner', 'Customer'),
        'address_id':fields.many2one('res.partner', 'Address'),
        'description':fields.char('Description', size=128),
        'cc_card_type' :fields.selection([('Discovery','Discovery'),
                                          ('AMEX','AMEX'),
                                          ('MasterCard','MasterCard'),
                                          ('Visa','Visa')],'Credit Card Type')
    }

    _defaults = {
        'partner_id' : _get_partner,
        'cc_card_type': 'Visa'
    }

    def request_to_server(self, Request_string, url, url_path):
        ''' Sends a POST request to url and returns the response from the server'''
#        url = 'https://apitest.authorize.net:80/xml/v1/request.api'
        conn = httplib.HTTPSConnection(url)
#        conn = urllib2.urlopen(url)
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

    def createCustomerPaymentProfile(self, dic):
            '''Creates  PaymentProfile for Customer  and returns the PaymentProfile id on success returns None or faliure '''
            KEYS = dic.keys()
            doc1 = Document()
            url_path = dic.get('url_extension', False)
            url = dic.get('url', False)
            xsd = dic.get('xsd', False)

            createCustomerPaymentProfileRequest = doc1.createElement("createCustomerPaymentProfileRequest")
            createCustomerPaymentProfileRequest.setAttribute("xmlns", xsd)
            doc1.appendChild(createCustomerPaymentProfileRequest)

            merchantAuthentication = doc1.createElement("merchantAuthentication")
            createCustomerPaymentProfileRequest.appendChild(merchantAuthentication)

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
                createCustomerPaymentProfileRequest.appendChild(customerProfileId)
                ptext = doc1.createTextNode(self._clean_string(dic['customerProfileId']))
                customerProfileId.appendChild(ptext)

            paymentProfile = doc1.createElement("paymentProfile")
            createCustomerPaymentProfileRequest.appendChild(paymentProfile)
            billTo = doc1.createElement("billTo")
            paymentProfile.appendChild(billTo)
            if 'firstName' in KEYS:
                firstName = doc1.createElement("firstName")
                billTo.appendChild(firstName)
                ptext = doc1.createTextNode(self._clean_string(dic['firstName']))
                firstName.appendChild(ptext)

            if 'lastName' in KEYS:
                lastName = doc1.createElement("lastName")
                billTo.appendChild(lastName)
                ptext = doc1.createTextNode(self._clean_string(dic['lastName']))
                lastName.appendChild(ptext)

            if 'company' in KEYS:
                company = doc1.createElement("company")
                billTo.appendChild(companycompany)
                ptext = doc1.createTextNode(self._clean_string(dic['company']))
                company.appendChild(ptext)

            if 'address' in KEYS:
                address = doc1.createElement("address")
                billTo.appendChild(address)
                ptext = doc1.createTextNode(self._clean_string(dic['address']))
                address.appendChild(ptext)
                
            if 'city' in KEYS:
                city = doc1.createElement("city")
                billTo.appendChild(city)
                ptext = doc1.createTextNode(self._clean_string(dic['city']))
                city.appendChild(ptext)

                ##State code must be given here
            if 'state' in KEYS:
                state = doc1.createElement("state")
                billTo.appendChild(state)
                ptext = doc1.createTextNode(self._clean_string(dic['state']))
                state.appendChild(ptext)

            if 'zip' in KEYS:
                zip = doc1.createElement("zip")
                billTo.appendChild(zip)
                ptext = doc1.createTextNode(self._clean_string(dic['zip']))
                zip.appendChild(ptext)

            if 'country' in KEYS:
                country = doc1.createElement("country")
                billTo.appendChild(country)
                ptext = doc1.createTextNode(self._clean_string(dic['country']))
                country.appendChild(ptext)

            if 'phoneNumber' in KEYS:
                phoneNumber = doc1.createElement("phoneNumber")
                billTo.appendChild(phoneNumber)
                ptext = doc1.createTextNode(self._clean_string(dic['phoneNumber']))
                phoneNumber.appendChild(ptext)

            if 'faxNumber' in KEYS:
                faxNumber = doc1.createElement("faxNumber")
                billTo.appendChild(faxNumber)
                ptext = doc1.createTextNode(self._clean_string(dic['faxNumber']))
                faxNumber.appendChild(ptext)

            payment = doc1.createElement("payment")
            paymentProfile.appendChild(payment)

            if 'cardNumber' in KEYS and 'expirationDate' in  KEYS:
                creditCard = doc1.createElement("creditCard")
                payment.appendChild(creditCard)

                cardNumber = doc1.createElement("cardNumber")
                creditCard.appendChild(cardNumber)
                ptext = doc1.createTextNode(dic['cardNumber'])
                cardNumber.appendChild(ptext)

                expirationDate = doc1.createElement("expirationDate")
                creditCard.appendChild(expirationDate)
                ptext = doc1.createTextNode(dic['expirationDate'])
                expirationDate.appendChild(ptext)

                if 'cardCode' in KEYS:
                                cardCode = doc1.createElement("cardCode")
                                creditCard.appendChild(cardCode)
                                ptext = doc1.createTextNode(self._clean_string(dic['cardCode']))
                                cardCode .appendChild(ptext)
                if 'bankAccount' in KEYS:
                                bankAccount = doc1.createElement("bankAccount")
                                creditCard.appendChild(bankAccount)
                                ptext = doc1.createTextNode(self._clean_string(dic['bankAccount']))
                                bankAccount .appendChild(ptext)

            if 'validationMode' in KEYS:
                validationMode = doc1.createElement("validationMode")
                createCustomerPaymentProfileRequest.appendChild(validationMode)
            
            ret = {}
            Request_string = xml = doc1.toxml(encoding="utf-8")
            create_CustomerPaymentProfile_response_xml = self.request_to_server(Request_string, url, url_path)
            create_CustomerPaymentProfile_response_dictionary = xml2dic.main(create_CustomerPaymentProfile_response_xml)
            parent_resultCode = self.search_dic(create_CustomerPaymentProfile_response_dictionary, 'resultCode')
            if parent_resultCode:
                if  parent_resultCode['resultCode'] == 'Ok':
                    parent_customerPaymentProfileId = self.search_dic(create_CustomerPaymentProfile_response_dictionary, 'customerPaymentProfileId')
                    return parent_customerPaymentProfileId['customerPaymentProfileId']
                else:
                    ret = {}
                    Error_Code_dic = self.search_dic(create_CustomerPaymentProfile_response_dictionary, 'code')
                    if Error_Code_dic.get('code'):
                        ret['Error_Code'] = Error_Code_dic['code']
                    Error_message_dic = self.search_dic(create_CustomerPaymentProfile_response_dictionary, 'text')
                    if  Error_message_dic.get('text'):
                        ret['Error_Message'] = Error_message_dic['text']
                    return ret
            return ret

    def createCustomerShippingAddressRequest(self, dic):
            '''Creates  shippingAddressRequest for Customer  and returns the shippingAddressRequest id on success returns None or failure '''
            KEYS = dic.keys()
            doc1 = Document()
            url_path = dic.get('url_extension', False)
            url = dic.get('url', False)
            xsd = dic.get('xsd', False)

            createCustomerShippingAddressRequest = doc1.createElement("createCustomerShippingAddressRequest")
            createCustomerShippingAddressRequest.setAttribute("xmlns", xsd)
            doc1.appendChild(createCustomerShippingAddressRequest)

            merchantAuthentication = doc1.createElement("merchantAuthentication")
            createCustomerShippingAddressRequest.appendChild(merchantAuthentication)

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
                createCustomerShippingAddressRequest.appendChild(customerProfileId)
                ptext = doc1.createTextNode(self._clean_string(dic['customerProfileId']))
                customerProfileId.appendChild(ptext)

            billTo = doc1.createElement("address")
            createCustomerShippingAddressRequest.appendChild(billTo)
            
            if 'firstName' in KEYS:
                firstName = doc1.createElement("firstName")
                billTo.appendChild(firstName)
                ptext = doc1.createTextNode(self._clean_string(dic['firstName']))
                firstName.appendChild(ptext)

            if 'lastName' in KEYS:
                lastName = doc1.createElement("lastName")
                billTo.appendChild(lastName)
                ptext = doc1.createTextNode(self._clean_string(dic['lastName']))
                lastName.appendChild(ptext)

            if 'company' in KEYS:
                company = doc1.createElement("company")
                billTo.appendChild(companycompany)
                ptext = doc1.createTextNode(self._clean_string(dic['company']))
                company.appendChild(ptext)

            if 'address' in KEYS:
                address = doc1.createElement("address")
                billTo.appendChild(address)
                ptext = doc1.createTextNode(self._clean_string(dic['address']))
                address.appendChild(ptext)
                
            if 'city' in KEYS:
                city = doc1.createElement("city")
                billTo.appendChild(city)
                ptext = doc1.createTextNode(self._clean_string(dic['city']))
                city.appendChild(ptext)

                ##State code must be given here
            if 'state' in KEYS:
                state = doc1.createElement("state")
                billTo.appendChild(state)
                ptext = doc1.createTextNode(self._clean_string(dic['state']))
                state.appendChild(ptext)

            if 'zip' in KEYS:
                zip = doc1.createElement("zip")
                billTo.appendChild(zip)
                ptext = doc1.createTextNode(self._clean_string(dic['zip']))
                zip.appendChild(ptext)

            if 'country' in KEYS:
                country = doc1.createElement("country")
                billTo.appendChild(country)
                ptext = doc1.createTextNode(self._clean_string(dic['country']))
                country.appendChild(ptext)

            if 'phoneNumber' in KEYS:
                phoneNumber = doc1.createElement("phoneNumber")
                billTo.appendChild(phoneNumber)
                ptext = doc1.createTextNode(self._clean_string(dic['phoneNumber']))
                phoneNumber.appendChild(ptext)

            if 'faxNumber' in KEYS:
                faxNumber = doc1.createElement("faxNumber")
                billTo.appendChild(faxNumber)
                ptext = doc1.createTextNode(self._clean_string(dic['faxNumber']))
                faxNumber.appendChild(ptext)

            ret = {}
            Request_string = xml = doc1.toxml(encoding="utf-8")
            print 'Request_string',Request_string
            createCustomerShippingAddress_response_xml = self.request_to_server(Request_string, url, url_path)
            createCustomerShippingAddress_response_dictionary = xml2dic.main(createCustomerShippingAddress_response_xml)
            parent_resultCode = self.search_dic(createCustomerShippingAddress_response_dictionary, 'resultCode')
            if parent_resultCode:
                if  parent_resultCode['resultCode'] == 'Ok':
                    parent_customerPaymentProfileId = self.search_dic(createCustomerShippingAddress_response_dictionary, 'customerAddressId')
                    return parent_customerPaymentProfileId['customerAddressId']
                else:
                    ret = {}
                    Error_Code_dic = self.search_dic(createCustomerShippingAddress_response_dictionary, 'code')
                    if Error_Code_dic.get('code'):
                        ret['Error_Code'] = Error_Code_dic['code']
                    Error_message_dic = self.search_dic(createCustomerShippingAddress_response_dictionary, 'text')
                    if  Error_message_dic.get('text'):
                        ret['Error_Message'] = Error_message_dic['text']
                    return ret
            return ret

    def create_payment_profile(self, cr, uid, ids, context=None):
        """
        Create new payment profile for the customer.
        """
        parent_model = context.get('active_model')
        parent_id = context.get('active_id')
        partner_obj = self.pool.get('res.partner')
        if parent_model == 'res.partner':
            partner = self.pool.get(parent_model).browse(cr, uid, parent_id)
            partner_id = parent_id
        else:
            partner = self.pool.get(parent_model).browse(cr, uid, parent_id).partner_id
            partner_id = partner.id
        data = self.pool.get('create.payment.profile').browse(cr, uid, ids[0])

        address = partner_obj.address_get(cr, uid, [partner_id], ['invoice'])
        addr_id = partner_obj.browse(cr, uid, address['invoice'])

        if not addr_id:
            raise osv.except_osv(_('Error!'), _('Please select Address in order to create customer payment profile'))

        if not partner.payment_profile_id:
            prof_id = partner_obj.create_cust_profile(cr, uid, [partner.id])
        else:
            prof_id = partner.payment_profile_id.name

        cardNumber = data.cc_number or ''
        cardCode = data.cc_verify_code or ''
        description = data.description or ''

        expirationDate = data.cc_ed_year + '-' + data.cc_ed_month

        Param_Dic = {}
        email = ''
        merchantCustomerId = ''
        description = ''

        Trans_key = partner.company_id.auth_config_id.transaction_key
        Login_id = partner.company_id.auth_config_id.login_id
        url_extension = partner.company_id.auth_config_id.url_extension
        xsd = partner.company_id.auth_config_id.xsd_link
        description += (partner.ref or '') + (partner.name or '')

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
            self._setparameter(Param_Dic, 'cardNumber', cardNumber)
            self._setparameter(Param_Dic, 'expirationDate', expirationDate)
            if addr_id:
                self._setparameter(Param_Dic, 'firstName', addr_id.name or '')
                self._setparameter(Param_Dic, 'address', addr_id.street or '')
                self._setparameter(Param_Dic, 'state', addr_id.state_id.name or '')
                self._setparameter(Param_Dic, 'zip', addr_id.zip or '')
                self._setparameter(Param_Dic, 'city', addr_id.city or '')
                self._setparameter(Param_Dic, 'country', addr_id.country_id.name or '')
                self._setparameter(Param_Dic, 'phoneNumber', addr_id.phone or '')
                self._setparameter(Param_Dic, 'faxNumber', addr_id.fax or '')
            if cardCode:
                self._setparameter(Param_Dic, 'cardCode', cardCode)
            self._setparameter(Param_Dic, 'customerProfileId', prof_id)
            self._setparameter(Param_Dic, 'description', description)

        Customer_Payment_Profile_ID = self.createCustomerPaymentProfile(Param_Dic)
        createCustomerShippingAddressRequest_ID = self.createCustomerShippingAddressRequest(Param_Dic)

        cust_prof_ids = self.pool.get('cust.profile').search(cr, uid, [('name', '=', prof_id)])
        cust_prof_id = cust_prof_ids and cust_prof_ids[0] or False
        if len(cust_prof_ids) > 0 and Customer_Payment_Profile_ID and type(Customer_Payment_Profile_ID) != type({}):
            
            cust_prof_id = self.pool.get('cust.payment.profile').create(cr, uid, {'name':Customer_Payment_Profile_ID,
                                                                               'cust_profile_id':cust_prof_id,
                                                                               'address_id':addr_id.id,
                                                                               'partner_id':partner_id,
                                                                               'cc_number' : len(data.cc_number) >=4 and data.cc_number[-4:] or 'XXXX',
                                                                               'cc_card_type': data.cc_card_type
                         })

        if len(cust_prof_ids) > 0 and createCustomerShippingAddressRequest_ID and type(createCustomerShippingAddressRequest_ID) != type({}):
            self.pool.get('cust.profile').write(cr, uid, cust_prof_ids, {'shipping_address_id':  createCustomerShippingAddressRequest_ID},context=context)

        return cust_prof_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
