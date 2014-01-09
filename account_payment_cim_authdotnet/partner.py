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
import httplib
from xml.dom.minidom import Document
import xml2dic
from tools.translate import _

class res_partner(osv.Model):
    _inherit = 'res.partner'
    _rec_name = 'payment_profile_id'
    _columns = {
        'payment_profile_id': fields.many2one('cust.profile', 'Payment Profiles', help='Store customers payment profile id', readonly='True'),
#        'payment_profile_ids':fields.one2many('cust.payment.profile', 'partner_id','Payment Profiles' ,help='Store customers payment profile id',readonly=True),
        'payment_profile_ids': fields.related('payment_profile_id', 'payment_profile_ids', type='one2many', relation='cust.payment.profile', string='Payment Profiles', readonly=True),
    }

    def request_to_server(self, Request_string, url, url_path):
        ''' Sends a POST request to url and returns the response from the server'''
        if ('http' or 'https') in url[:5]:
            raise osv.except_osv(_('Configuration Error!'), _('Request URL should not start with http or https.\nPlease check Authorization Configuration in Company.'))
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

    def createCustomerProfile(self, dic):
        '''Creates  CustomerProfile and returns the CustomerProfile id on success returns None or faliure '''

        dic.update({'merchantCustomerId': '1'})
        KEYS = dic.keys()
        doc1 = Document()
        url_path = dic.get('url_extension', False)
        url = dic.get('url', False)
        xsd = dic.get('xsd', False)

        createCustomerProfileRequest = doc1.createElement("createCustomerProfileRequest")
        createCustomerProfileRequest.setAttribute("xmlns", xsd)
        doc1.appendChild(createCustomerProfileRequest)
        
        merchantAuthentication = doc1.createElement("merchantAuthentication")
        createCustomerProfileRequest.appendChild(merchantAuthentication)

        name = doc1.createElement("name")
        merchantAuthentication.appendChild(name)

        transactionKey = doc1.createElement("transactionKey")
        merchantAuthentication.appendChild(transactionKey)
        
        ##Create the Request for creating the customer profile
        if 'api_login_id' in KEYS and 'transaction_key' in KEYS:

            ptext1 = doc1.createTextNode(self._clean_string(dic['api_login_id']))
            name.appendChild(ptext1)

            ptext = doc1.createTextNode(self._clean_string(dic['transaction_key']))
            transactionKey.appendChild(ptext)
            
        if 'refId' in KEYS:
            refId = doc1.createElement("refId")
            ptext1 = doc1.createTextNode(self._clean_string(dic['refId']))
            refId.appendChild(ptext1)
            createCustomerProfileRequest.appendChild(refId)
            

        ##Now Add Profile INformation for the user
        profile = doc1.createElement("profile")
        createCustomerProfileRequest.appendChild(profile)

        if 'merchantCustomerId' in KEYS:
            merchantCustomerId = doc1.createElement("merchantCustomerId")
            profile.appendChild(merchantCustomerId)
            ptext = doc1.createTextNode(dic['merchantCustomerId'])
            merchantCustomerId.appendChild(ptext)

        if 'description' in KEYS:
            description = doc1.createElement("description")
            profile.appendChild(description)
            ptext = doc1.createTextNode(dic['description'])
            description.appendChild(ptext)

        if 'email' in KEYS:
            email = doc1.createElement("email")
            profile.appendChild(email)
            ptext = doc1.createTextNode(dic['email'])
            email.appendChild(ptext)


        if 'paymentProfiles' in KEYS:
            paymentProfiles = doc1.createElement("paymentProfiles")
            profile.appendChild(paymentProfiles)
            ptext1 = doc1.createTextNode(self._clean_string(dic['paymentProfiles']))
            paymentProfiles.appendChild(ptext1)

#########        TO DO ADD THE NECCESSARY OPTIONS INTO IT

#        Request_string1=xml=doc1.toprettyxml( encoding="utf-8" )
        Request_string = xml = doc1.toxml(encoding="utf-8")
        #Select from production and test server
        create_CustomerProfile_response_xml = self.request_to_server(Request_string, url, url_path)
        create_CustomerProfile_response_dictionary = xml2dic.main(create_CustomerProfile_response_xml)
        parent_msg = self.search_dic(create_CustomerProfile_response_dictionary, "messages")
        if parent_msg['messages'][0]['resultCode'] == 'Ok':
            parent = self.search_dic(create_CustomerProfile_response_dictionary, "customerProfileId")
            return parent['customerProfileId']

        return {'Error_Code':parent_msg['messages'][1]['message'][0]['code'],
                    'Error_Message' :parent_msg['messages'][1]['message'][1]['text']}

    def create_cust_profile(self, cr, uid, ids, address_id=False, context=None):
        if not context: context = {}
        ret = {}
        Param_Dic = {}
        email = ''
        merchantCustomerId = ''
        description = ''
        cust_obj = self.pool.get('res.partner')
        cust_prof_obj = self.pool.get('cust.payment.profile')
        customers = cust_obj.browse(cr, uid, ids)
        
        # Creating the customer profile 
        for customer in customers:
            Trans_key = customer.company_id.auth_config_id.transaction_key or ''
            Login_id = customer.company_id.auth_config_id.login_id or ''
            url_extension = customer.company_id.auth_config_id.url_extension or ''
            xsd = customer.company_id.auth_config_id.xsd_link or ''
            description += (customer.ref or '') + (customer.name or '')
            if customer.company_id.auth_config_id.test_mode:
                url = customer.company_id.auth_config_id.url_test or ''
            else:
                url = customer.company_id.auth_config_id.url or ''

            if not address_id:
                address = cust_obj.address_get(cr, uid, [customer.id], ['invoice'])
                address = cust_obj.browse(cr, uid, address['invoice'])
            else:
                address = cust_obj.browse(cr, uid, address_id)

            email = address.email or ''
            if Trans_key and Login_id:
                self._setparameter(Param_Dic, 'api_login_id', Login_id)
                self._setparameter(Param_Dic, 'transaction_key', Trans_key)

                self._setparameter(Param_Dic, 'email', email)
                self._setparameter(Param_Dic, 'description', description)
                self._setparameter(Param_Dic, 'merchantCustomerId', merchantCustomerId)

                if url:
                    self._setparameter(Param_Dic, 'url', url)
                    self._setparameter(Param_Dic, 'url_extension', url_extension)
                if xsd:
                    self._setparameter(Param_Dic, 'xsd', xsd)
                Customer_Profile_ID = self.createCustomerProfile(Param_Dic)
                if Customer_Profile_ID and type(Customer_Profile_ID) == type(''):
                    cust_prof_id = self.pool.get('cust.profile').create(cr, uid, {'name':Customer_Profile_ID})
                    cust_obj.write(cr, uid, ids, {'payment_profile_id':cust_prof_id})
#                     self._setparameter(Param_Dic, 'customerProfileId', Customer_Profile_ID)
                    return Customer_Profile_ID
                else:
                    raise osv.except_osv(_('Transaction Error in Creating Customer Profile ID'), _('Error code : ' + Customer_Profile_ID['Error_Code'] + '\nError Message :' + Customer_Profile_ID['Error_Message']))
            else:
                raise osv.except_osv(_('Transaction Error'), _('Cannot process without valid Transaction Key and/or Login ID.Please check the configuration'))

        return ret

res_partner()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
