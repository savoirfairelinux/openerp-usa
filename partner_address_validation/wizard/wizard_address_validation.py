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


class address_validation_response_data(orm.TransientModel):
    '''
    Class to store address details returned from ups
    '''
    _name = "response.data.model"
    _rec_name = "street1"
    _columns = {
        'street1': fields.char('Street1', size=32, required=True, select=1),
        'city': fields.char('City', size=32, required=True, select=1),
        'state': fields.char('State', size=32, required=True, select=1),
        'zip': fields.char('Zip', size=32, required=True, select=1),
        'classification' :  fields.selection([('',''),('0','Unknown'),('1','Commercial'),('2','Residential')], 'Classification'),
        'so_validate_inv':fields.many2one("so.addr_validate","Sale Order Validate"),
        'so_validate_ord':fields.many2one("so.addr_validate","Sale Order Validate"),
        'so_validate_ship':fields.many2one("so.addr_validate","Sale Order Validate"),
        'so_validate':fields.integer("Sale Order Validate"),
        'select':fields.boolean("Select")
    }
address_validation_response_data()


class partner_addr_validate(orm.TransientModel):
    '''
    Wizard object to validate address of partner address
    '''
    _name = "partner.addr_validate"
    _description = "Partner Address Validate"
#    _rec_name = 'inv_error_msg'

    def clean_memory(self, cr, uid):
        resp_pool = self.pool.get('response.data.model')
        resp_ids = resp_pool.search(cr, uid, [])
        resp_pool.unlink(cr, uid, resp_ids)
        return True

    def get_state(self,cr, uid, state): # not required any more
        """ Returns the state_id,by taking the state code as an argument """
        states = self.pool.get('res.country.state').search(cr,uid,['|',('name','=',state),('code','=',state)])
        return states and states[0] or False

    def get_zip(self,cr, uid,zip,state,city): # not required any more
        """ Returns the id of the correct address.zip model """
        state_id=self.get_state(cr,uid,state)
        ids=self.pool.get('address.zip').search(cr,uid,[('zipcode','=',zip),
                                                  ('state_id','=',state_id),
                                                  ('city','=',city)])
        return ids
    
    def do_write(self, cr, uid, address_id, address_list, context={}):
        address_vals = {}
        for address_item in address_list:
            if address_item.select:
                state=address_item.state
                state_id=self.get_state(cr,uid,state)
                
                address_vals = {
                    'street':address_item.street1,
                    'city':address_item.city,
                    'state_id':state_id,
                    'last_address_validation': time.strftime('%Y-%m-%d'),
                    'classification': address_item.classification,
                    'zip':address_item.zip
                }
#                zip_id=self.get_zip(cr, uid,address_item.zip,state,address_item.city)
                
#                if len(zip_id) == 1:
#                    address_vals['zip_id'] = zip_id[0]
#                    address_vals['zip'] = address_item.zip
                break
#        address_vals and self.pool.get('res.partner').write(cr,uid,address_id, address_vals)
        address_vals and self.pool.get('res.partner').write(cr,uid,context['active_id'], address_vals)
        cr.commit()
        self.clean_memory(cr, uid)
        return True

    def update_address(self, cr, uid, ids, context=None):
        
        """ To write the selected address to the partner address form """
        datas = self.browse(cr,uid,ids,context=context)
        for data in datas:
            self.do_write(cr, uid, data.id, data.address_list, context=context)
        return {}

    def onchange_update(self, cr, uid, ids, default_addr_id, context=None):
        ret = {}
        if default_addr_id:
            address_item = self.pool.get('res.partner').browse(cr,uid,default_addr_id )
            if address_item.address_validation_method is 'none':
                return { 'value':ret }
            inv_return_data = self.pool.get(address_item.address_validation_method).address_validation(cr, uid, default_addr_id, context=context)
            ret['error_msg'] = inv_return_data['error_msg']
            ret['address_list'] = inv_return_data['address_list']
            ret['address_id'] = default_addr_id
        return {'value':ret}

    _columns = {
        'error_msg': fields.text('Error Message'),
        'address_list':fields.one2many('response.data.model','so_validate', 'Address List'),
        'address_id':fields.many2one('res.partner','Address'),
    }

partner_addr_validate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
