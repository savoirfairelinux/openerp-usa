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

class shipping_move(osv.osv):
    _name = "shipping.move"
    _rec_name = 'pick_id'
    _columns = {
        'pick_id': fields.many2one("stock.picking", 'Delivery Order'),
        'pic_date': fields.datetime('Pickup Date'),
        'ship_date': fields.datetime('Shipping Date'),
        'logis_company': fields.many2one('res.company', 'Logistics Company', help='Name of the Logistics company providing the shipper services.'),
        'package_weight': fields.float('Package Weight'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('in_process', 'In Process'),
            ('ready_pick', 'Ready for Pickup'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('hold', 'Hold'),
            ('void', 'Void'),
            ('cancelled', 'Cancelled')
            ], 'Shipping Status', readonly=True, help='The current status of the shipment'),
        'tracking_no': fields.char('Tracking', size=128,),
        'ship_to': fields.many2one('res.partner', 'Ship To'),
        'package': fields.char('Package', size=128),
        'ship_cost': fields.float('Shipment Cost'),
        'ship_from': fields.many2one('res.partner', 'Ship From' ),
        'freight': fields.boolean('Shipment', help='Indicates if the shipment is a freight shipment.'),
        'sat_delivery': fields.boolean('Saturday Delivery', help='Indicates is it is appropriate to send delivery on Saturday.'),
        'package_type': fields.selection([('', '')] ,'Package Type', help='Indicates the type of package'),
        'bill_shipping': fields.selection([
            ('shipper', 'Shipper'),
            ('receiver', 'Receiver'),
            ('thirdparty', 'Third Party')
            ],'Bill Shipping to', help='Shipper, Receiver, or Third Party.'),
        'with_ret_service': fields.boolean('With Return Services', help='Include Return Shipping Information in the package.'),
        'trade_mark': fields.text('Trademarks AREA'),
        'packages_ids': fields.one2many("stock.packages", 'ship_move_id', 'Packages Table'),
        'partner_id': fields.many2one("res.partner", 'Customer/Reseller'),
        'sale_id': fields.many2one('sale.order', 'Sale Order'),
    }
    _defaults = {
        'bill_shipping': 'shipper'
    }

    def write(self, cr, uid, ids, vals, context=None):
        res = super(shipping_move, self).write(cr, uid, ids, vals, context=context)
        if 'state' in vals:
            pick_ids = []
            if 'pick_id' in vals:
                pick_ids.append(vals['pick_id'])
            else:
                for log_obj in self.browse(cr, uid, ids, context=context):
                    if log_obj.pick_id:
                        pick_ids.append(log_obj.pick_id.id)
            self.pool.get("stock.picking").write(cr, uid, pick_ids, {'ship_state': vals['state']}, context=context)
        return res
    
    def create(self, cr, uid, vals, context=None):
        move_id = super(shipping_move, self).create(cr, uid, vals, context=context)
        if 'state' in vals:
            pick_ids = []
            if 'pick_id' in vals:
                pick_ids.append(vals['pick_id'])
                self.pool.get("stock.picking").write(cr, uid, pick_ids, {'ship_state': vals['state']}, context=context)
        return move_id

shipping_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: