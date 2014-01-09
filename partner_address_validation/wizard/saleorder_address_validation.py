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

from openerp.osv import orm, fields, osv
import time
from openerp.tools.translate import _
# import pdb


class so_addr_validate(orm.TransientModel):
    '''
    Wizard object to validate address of sale order
    '''
    _name = "so.addr_validate"
    _description = "Sale order Address Validate"
    _rec_name = 'inv_error_msg'

    def clean_memory(self, cr, uid):
        resp_pool = self.pool.get('response.data.model')
        resp_ids = resp_pool.search(cr, uid, [])
        resp_pool.unlink(cr, uid, resp_ids)
        
        resp_pool = self.pool.get('so.addr_validate')
        resp_ids = resp_pool.search(cr, uid, [])
        resp_pool.unlink(cr, uid, resp_ids)
        return True

    def get_state(self,cr, uid, state, context=None): # not required any more
        """ Returns the state_id,by taking the state code as an argumrnt """
        states = self.pool.get('res.country.state').search(cr,uid,['|',('name','=',state),('code','=',state)])
        return states and states[0] or False
    
    def get_zip(self,cr, uid,zip,state,city): # not required any more
        """ Returns the id of the correct address.zip model """
        state_id= self.get_state(cr,uid,state)
        ids= self.pool.get('address.zip').search(cr,uid,[('zipcode','=',zip),
                                                        ('state_id','=',state_id),
                                                        ('city','=',city)])
        return ids

    def do_write(self, cr, uid, address_id, address_list, context={}):
        address_vals = {}
        for address_item in address_list:
            if address_item.select:
                state=address_item.state
                state_id=self.get_state(cr,uid,state,context)
                address_vals = {'street':address_item.street1,
                                'city':address_item.city,
                                'state_id':state_id,
                                'last_address_validation': time.strftime('%Y-%m-%d'),
                                'classification'  : address_item.classification,
                                'zip': address_item.zip
                              }
#                zip_id=self.get_zip(cr, uid,address_item.zip,state,address_item.city)
#                if len(zip_id) == 1:
#                    address_vals['zip_id'] = zip_id[0]
                break
#                    address_vals['zip'] = address_item.zip
        address_vals and self.pool.get('res.partner').write(cr,uid,address_id, address_vals)
        return True

    def update_address(self, cr, uid, ids, context=None):
        datas = self.browse(cr,uid,ids,context=context)
        for data in datas:
            self.do_write(cr, uid, data.inv_address_id.id, data.inv_address_list, context=context)
            
            if data.inv_address_id.id != data.ord_address_id.id:
                self.do_write(cr, uid, data.ord_address_id.id, data.ord_address_list, context=context)
            
            if data.inv_address_id.id != data.ship_address_id.id and data.ord_address_id.id != data.ship_address_id.id:
                self.do_write(cr, uid, data.ship_address_id.id, data.ship_address_list, context=context)
        self.clean_memory(cr, uid)
        return {}

    def onchange_update(self, cr, uid, ids, sale_id, context=None):
            ret = {}
            if sale_id:
                res = self.pool.get('sale.order').read(cr, uid, sale_id, ['partner_invoice_id', 'partner_shipping_id','address_validation_method', 'partner_id'])
                inv_addr_id = res['partner_invoice_id']
                ord_addr_id = res['partner_id']
                ship_addr_id = res['partner_shipping_id']
                validation_method = res['address_validation_method']
               
#                 pdb.set_trace()
                inv_return_data = self.pool.get(validation_method).address_validation(cr, uid, inv_addr_id, context=context)
                if inv_return_data['address_list']:
                    inv_return_data['address_list'][0]['select']=True
                ret['inv_error_msg'] = inv_return_data['error_msg']
                if inv_return_data['address_list']:
                    ret['inv_address_list'] = inv_return_data['address_list']
               
                if inv_addr_id == ord_addr_id:
                    ord_return_data = inv_return_data
               
                if inv_addr_id == ship_addr_id:
                    ship_return_data = inv_return_data
                elif ord_addr_id == ship_addr_id:
                    ship_return_data = ord_return_data
                else:
                    ship_return_data = self.pool.get(validation_method).address_validation(cr, uid, ship_addr_id, context=context)
                    if ship_return_data['address_list']:
                        ship_return_data['address_list'][0]['select']=True
                ret['ship_error_msg'] = ship_return_data['error_msg']
                if ship_return_data['address_list']:
                    ret['ship_address_list'] = ship_return_data['address_list']

                ret['inv_address_id'] = inv_addr_id
                ret['ord_address_id'] = ord_addr_id
                ret['ship_address_id'] = ship_addr_id
            return {'value':ret}


    _columns = {
        'update_field':fields.boolean('Update'),
        'sale_id':fields.many2one('sale.order','Sale Order'),

        'inv_error_msg': fields.text('Status', size=35 , readonly= True),
        'ord_error_msg': fields.text('Status' ,size=35, readonly= True),
        'ship_error_msg': fields.text('Status' ,size=35 ,readonly= True),

        'inv_address_list':fields.one2many('response.data.model','so_validate_inv', 'Invoice Address List'),
        'ord_address_list':fields.one2many('response.data.model','so_validate_ord', 'Order Address List'),
        'ship_address_list':fields.one2many('response.data.model','so_validate_ship', 'Ship Address List'),

        'inv_address_id':fields.many2one('res.partner','Invoice Address'),
        'ord_address_id':fields.many2one('res.partner','Order Address'),
        'ship_address_id':fields.many2one('res.partner','Ship Address'),
    }

so_addr_validate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
