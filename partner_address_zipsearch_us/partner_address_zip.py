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
from tools.translate import _

class res_partner_address(osv.osv):
    '''
        New localtion fields and zip field as a many2one
    '''
    _description ='Partner Addresses'
    _inherit='res.partner'
    
    _columns = {
        'longitude':fields.char('Longitude', size=64,),
        'latitude':fields.char('Latitude', size=64,),
        'zip_id':fields.many2one("address.zip", "Zip"),
        'zip': fields.char('ZIP', change_default=True, size=24),
        }

    def on_change_zip(self, cr, uid, id, zip, context=None):
        '''
            location details from new zip field (many2one)
        '''
        if context is None: context = {} 
        company_obj = self.pool.get('res.users').browse(cr, uid, uid,context=context).company_id
        if not company_obj.lzipmatch:
            return {'value': {}}
        if not zip:
            return {'value': {'zip' : ''}}

        zip = self.pool.get('address.zip').browse(cr, uid, zip, context=context)
        vals = {
            'longitude': zip.longitude,
            'latitude': zip.latitude,
            'city': zip.city,
            'state_id': zip.state_id.id,
            'country_id': zip.state_id.country_id.id,
            'zip': zip.zipcode,
            }
        return {'value': vals}

    def create(self, cr, uid, vals, context=None):
        if 'zip' in vals:
            zipcode = vals['zip']
            zip_ids = self.pool.get('address.zip').search(cr, uid, [('zipcode', '=', zipcode)], context=context)
            zip_id = zip_ids and zip_ids[0] or False
            if zip_id:
                if not 'zip_id' in vals:
                    zip = self.pool.get('address.zip').browse(cr, uid, zip_id, context=context)
                    vals.update({
                        'longitude': zip.longitude,
                        'latitude': zip.latitude,
                        'city': zip.city,
                        'state_id': zip.state_id.id,
                        'country_id': zip.state_id.country_id.id,
                        'zip_id': zip_id
                        })
                    return super(res_partner_address, self).create(cr, uid, vals, context)
        return super(res_partner_address, self).create(cr, uid, vals, context)

res_partner_address()

    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
