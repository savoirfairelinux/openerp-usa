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
from openerp.tools.translate import _
import time

def _method_get(self, cr, uid, context=None):
    list = [('none',''),("", "")]
    ups_acc_obj = self.pool.get('ups.account')
    fedex_acc_obj = self.pool.get('fedex.account')
    usps_acc_obj = self.pool.get('usps.account')
    ups_ids = ups_acc_obj.search(cr, uid, [])
    fedex_ids = fedex_acc_obj.search(cr, uid, [])
    usps_ids = usps_acc_obj.search(cr, uid, [])

    if ups_ids:
        list.append(('ups.account','UPS'))

    if fedex_ids:
        list.append(('fedex.account','FedEx'))

    if usps_ids:
        list.append(('usps.account','USPS'))
    return list

class res_partner(osv.osv):
    _description ='Partner Addresses'
    _inherit='res.partner'
    _columns = {
        'last_address_validation': fields.date('Last Address Validation', readonly=True),
        'address_validation_method': fields.selection(_method_get, 'Address Validation Method', size=32),
        'classification': fields.selection([('',''),('0','Unknown'),('1','Commercial'),('2','Residential')], 'Classification'), 
    }

    '''
    Change the address disply as us format
    '''
    
    def _get_address_validation_method(self, cr, uid, context={}):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user and user.company_id and user.company_id.address_validation_method
    
    _defaults = {
#        'address_validation_method': _get_address_validation_method,
    }

res_partner()

class sale_order(osv.osv):
    
    _inherit='sale.order'
    '''
    Add address validation fields on sale order
    '''

    def so_addr_validate_wiz(self, cr, uid, ids, context=None):
        obj_model = self.pool.get('ir.model.data')
        
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_so_addrvalidate')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'so.addr_validate',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }

    def _validated(self, cr, uid, ids, name, args, context=None):
        res = {}
        for sale_order in self.browse(cr,uid,ids,context=context):
            if sale_order.partner_invoice_id.last_address_validation and sale_order.partner_order_id.last_address_validation and sale_order.partner_shipping_id.last_address_validation:
                res[sale_order.id] = True
            else:
                res[sale_order.id] = False
        return res

    _columns={  
        'hide_validate':fields.function(_validated, method=True, string='Hide Validate', type='boolean', store=False),
        'address_validation_method': fields.selection(_method_get, 'Address Validation Method', size=32),
    }

    def _get_address_validation_method(self, cr, uid, context=None):
        if context is None: context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user and user.company_id and user.company_id.address_validation_method
    
    _defaults = {
        'address_validation_method':_get_address_validation_method,
    }

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
