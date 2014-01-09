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

from openerp.osv import fields,osv
# import pdb

class usps_account(osv.osv):
    '''
        USPS Account details
    '''
    _name = "usps.account"

    _columns = {
        'name' : fields.char('Company Name', size=64),
        'usps_userid' : fields.char('User ID', size=64),
        'usps_url_test' : fields.char('Test URL', size=512),
        'usps_url' : fields.char('Production URL', size=512),
        'test_mode' : fields.boolean('Test Mode'),
    }

    _defaults  = {
        'test_mode' : lambda * a: True,
    }

    def address_validation(self,cr, uid, address_id, context={}):

#         pdb.set_trace()
        """ This function is called from the wizard.Performs the actual computing in address validation """
        status=0
        error_msg=''
        usps_accounts = self.pool.get('usps.account').search(cr, uid, [], context={})
        if not usps_accounts:
            warning = {
                'title': "No USPS account!",
                'message': "No USPS account found for validation."
            }
            return {'warning': warning} 

        if usps_accounts and address_id:
            usps_account = self.pool.get('usps.account').browse(cr, uid, usps_accounts[0], context=context)
            if type(address_id) is list or type(address_id) is tuple:
                address_id=address_id[0]

            partner_address = self.pool.get('res.partner').browse(cr, uid, address_id, context=context)
            
            url = usps_account.test_mode and usps_account.usps_url_test or usps_account.usps_url
            userid = usps_account.usps_userid or ''

            from usps.addressinformation import base
            
            connector = base.AddressValidate(url)
            ret_list = []
            try:
                response = connector.execute(userid, [{'Address2':partner_address.street,
                                                           'City':partner_address.city,
                                                           'State':partner_address.state_id and partner_address.state_id.code or '',
                                                           'Zip5': partner_address.zip or ''
                                                           }])[0]


                error_msg = "Success: Address is valid."

            except base.USPSXMLError, e:
                error_msg =  error_msg + str(e)

            except Exception, e:

                error_msg =  error_msg + str(e)
            return {
                'addr_status':status,
                'error_msg':error_msg,
                'address_list':ret_list
            }

usps_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
