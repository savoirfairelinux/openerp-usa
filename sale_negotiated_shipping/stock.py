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

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    def _get_sale_order(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').search(cr, uid, [('sale_id', 'in', ids)])
    
    _columns = {
        'ship_method': fields.related('sale_id', 'ship_method', string='Name', type='char', size=128,
            store = {'sale.order': (_get_sale_order, ['ship_method'], -10)})
    }

stock_picking()

class stock_picking(osv.osv):
    _inherit = "stock.picking.out"
    
    def _get_sale_order(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking.out').search(cr, uid, [('sale_id', 'in', ids)])
    
    _columns = {
        'ship_method': fields.related('sale_id', 'ship_method', string='Name', type='char', size=128,
            store = {'sale.order': (_get_sale_order, ['ship_method'], -10)})
    }

stock_picking()

class stock_move(osv.osv):
    _inherit = "stock.move"
    
    def _get_sale_order(self, cr, uid, ids, context=None):
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('sale_id', 'in', ids)])
        move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', picking_ids)])
        return move_ids
    
    _columns = {
        'ship_method': fields.related('picking_id', 'sale_id', 'ship_method', string='Name', type='char', size=128,
            store = {'sale.order': (_get_sale_order, ['ship_method'], -10)})
    }

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: