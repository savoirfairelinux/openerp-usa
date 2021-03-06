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

class purchase_order(osv.osv):
       
    _inherit = "purchase.order"
       
    def _get_warehouse(self, cr, uid, ids, context=None):
        res = self.pool.get('stock.warehouse').search(cr, uid, [])
        return res and res[0] or False 
       
    _defaults = {
        'warehouse_id': _get_warehouse,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: