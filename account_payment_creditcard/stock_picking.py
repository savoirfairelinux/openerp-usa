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
    '''
    Adding credit card preauthorised and payed check box on delivery order
    '''
    def _get_sale_order(self, cr, uid, ids, context={}):
        result = []
        move_ids = []
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        for id in ids:
            stock_pick_ids = picking_obj.search(cr, uid, [('sale_id', '=', id)])
            if stock_pick_ids:
                move_ids += move_obj.search(cr, uid, [('picking_id', 'in', stock_pick_ids)])
        move_ids = list(set(move_ids))
        return move_ids
    
    _columns = {
        'cc_pre_auth':  fields.related('sale_id', 'cc_pre_auth', string='CC Pre-authorised', type='boolean'),
        'invoiced':  fields.related('sale_id', 'invoiced', string='Paid', type='boolean'),
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable"),
            ("credit_card", "Credit Card"),
            ("cc_refund", "Credit Card Refund")
            ], "Invoice Control", select=True, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'ship_state': fields.selection([
            ('draft', 'Draft'),
            ('in_process', 'In Process'),
            ('ready_pick', 'Ready for Pickup'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('void', 'Void'),
            ('hold', 'Hold'),
            ('cancelled', 'Cancelled')
            ], 'Shipping Status', readonly=True, help='The current status of the shipment'),
        'ship_message': fields.text('Message'),
    }

stock_picking()

class stock_picking_out(osv.osv):

    _inherit = "stock.picking.out"
    
    _columns = {
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable"),
            ("credit_card", "Credit Card"),
            ("cc_refund", "Credit Card Refund")
            ], "Invoice Control", select=True, required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }
    
class stock_picking_in(osv.osv):

    _inherit = "stock.picking.in"
    
    _columns = {
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable"),
            ("credit_card", "Credit Card"),
            ("cc_refund", "Credit Card Refund")
            ], "Invoice Control", select=True, required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
