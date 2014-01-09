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

class fedex_account(osv.osv):
    
    _name = "fedex.account"
    '''
    FedEx Account details
    '''
    _columns = {
        'name' : fields.char('Comapny Name', size=64),
        'fedex_key' : fields.char('FedEx Key', size=64),
        'fedex_password': fields.char('Password', size=128),
        'fedex_account_number' : fields.char('Account Number', size=64),
        'fedex_meter_number' : fields.char('Meter Number', size=64),
        'test_mode' : fields.boolean('Test Mode'),
    }

    _defaults = {
        'test_mode' : lambda * a: True,
    }

    def address_validation(self, cr, uid, address_id, context={}):
        """ This function is called from the wizard.Performs the actual computing in address validation """
        status = 0
        error_msg = ''
        
        fedex_accounts = self.pool.get('fedex.account').search(cr, uid, [], context={})
        if not fedex_accounts:
            warning = {
                'title': "No FedEx account!",
                'message': "No FedEx account found for validation."
            }
            return {'warning': warning} 
        if fedex_accounts and address_id:
            fedex_account = self.pool.get('fedex.account').browse(cr, uid, fedex_accounts[0], context=context)
            if type(address_id) == type([]):
                address_id = address_id[0]
            partner_address = self.pool.get('res.partner').browse(cr, uid, address_id, context=context)
            from fedex.config import FedexConfig
            config_obj = FedexConfig(key=fedex_account.fedex_key,
                             password=fedex_account.fedex_password,
                             account_number=fedex_account.fedex_account_number,
                             meter_number=fedex_account.fedex_meter_number,
                             use_test_server=fedex_account.test_mode)
            from fedex.services.address_validation_service import FedexAddressValidationRequest
            
            address = FedexAddressValidationRequest(config_obj)

            address1 = address.create_wsdl_object_of_type('AddressToValidate')
            address1.CompanyName = partner_address.name or ''
            address1.Address.StreetLines = [ partner_address.street, partner_address.street2 ]
            address1.Address.City = partner_address.city
            address1.Address.StateOrProvinceCode = partner_address.state_id and partner_address.state_id.code or ''
            address1.Address.PostalCode = partner_address.zip
            address1.Address.CountryCode = partner_address.country_id and  partner_address.country_id.code or ''
            address1.Address.Residential = False
            
            address.add_address(address1)
            
            ret_list = []
            try:
                address.send_request()
                response = address.response
                #Possible values ERROR, FAILURE, NOTE, WARNING, SUCCESS
                if response.HighestSeverity == 'SUCCESS':
                    error_msg = "The address is valid"
                    status = 1
                elif response.HighestSeverity == 'ERROR' or response.HighestSeverity == 'FAILURE':
                    error_msg = str(response.Notifications[0].Message)
            except Exception, e:
                error_msg = error_msg + str(e)
            return {
                'addr_status':status,
                'error_msg':error_msg,
                'address_list':ret_list
            }

fedex_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
