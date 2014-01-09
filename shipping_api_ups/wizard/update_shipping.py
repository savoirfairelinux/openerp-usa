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

import time

from openerp.osv import orm, osv, fields

class partner_addr_validate(orm.TransientModel):
    '''
    Wizard object to update shipping status
    '''
    _name = "ship.status"
    _description = "Update Shipping status"
    _rec_name = 'status'
    _columns = {
        'status': fields.selection([   
            ('draft', 'Draft'),
            ('in_process', 'In Process'),
            ('ready_pick', 'Ready for Pickup'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('void', 'Void'),
            ('hold', 'Hold'),
            ('cancelled', 'Cancelled')
        ], 'New Status')
    }

    def update_status(self, cr, uid, ids, context=None):
        vals= {}
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids[0], context=context)
        if data and data.status and context.get('active_ids'):
            vals['state'] = data.status
            if data.status == 'shipped':
                vals['ship_date'] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.pool.get('shipping.move').write(cr, uid, context['active_ids'], vals)
        return vals

partner_addr_validate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: