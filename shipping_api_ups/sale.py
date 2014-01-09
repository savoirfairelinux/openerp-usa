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

class sale_order(osv.osv):
    _inherit = "sale.order"

    def action_ship_create(self, cr, uid, ids, context=None):
        pick_obj = self.pool.get('stock.picking')
        result = super(sale_order, self).action_ship_create(cr, uid, ids, context=context)
        if result:
            for sale in self.browse(cr, uid, ids):
                if sale.ship_company_code == 'ups':
                    pick_ids = pick_obj.search(cr, uid, [('sale_id', '=', sale.id), ('type', '=', 'out')], context=context)
                    if pick_ids:
                        vals = {
                            'ship_company_code': 'ups',
                            'logis_company': sale.logis_company and sale.logis_company.id or False,
                            'shipper': sale.ups_shipper_id and sale.ups_shipper_id.id or False,
                            'ups_service': sale.ups_service_id and sale.ups_service_id.id or False,
                            'ups_pickup_type': sale.ups_pickup_type,
                            'ups_packaging_type': sale.ups_packaging_type and sale.ups_packaging_type.id or False,
                            'ship_from_address':sale.ups_shipper_id and sale.ups_shipper_id.address and sale.ups_shipper_id.address.id or False,
                            'shipcharge':sale.shipcharge or False
                            }
                        pick_obj.write(cr, uid, pick_ids, vals)
                else:
                    pick_ids = pick_obj.search(cr, uid, [('sale_id', '=', sale.id), ('type', '=', 'out')])
                    if pick_ids:
                        pick_obj.write(cr, uid, pick_ids, {'shipper': False, 'ups_service': False}, context=context)
        return result

    def _get_company_code(self, cr, user, context=None):
        res = super(sale_order, self)._get_company_code(cr, user, context=context)
        res.append(('ups', 'UPS'))
        return res
    
    def onchage_service(self, cr, uid, ids, ups_shipper_id=False, context=None):
         vals = {}
         service_type_ids = []
         if ups_shipper_id:
             shipper_obj = self.pool.get('ups.account.shipping').browse(cr, uid, ups_shipper_id)
             for shipper in shipper_obj.ups_shipping_service_ids:
                 service_type_ids.append(shipper.id)
         domain = [('id', 'in', service_type_ids)]
         return {'domain': {'ups_service_id': domain}}
    
    _columns = {
        'payment_method':fields.selection([
            ('cc_pre_auth', 'Credit Card – PreAuthorized'),
            ('invoice', 'Invoice'),
            ('cod', 'COD'),
            ('p_i_a', 'Pay In Advance'),
            ('pay_pal', 'Paypal'),
            ('no_charge', 'No Charge')], 'Payment Method'),
        'ship_company_code': fields.selection(_get_company_code, 'Logistic Company', method=True, size=64),
        'ups_shipper_id': fields.many2one('ups.account.shipping', 'Shipper'),
        'ups_service_id': fields.many2one('ups.shipping.service.type', 'Service Type'),
        'ups_pickup_type': fields.selection([
            ('01', 'Daily Pickup'),
            ('03', 'Customer Counter'),
            ('06', 'One Time Pickup'),
            ('07', 'On Call Air'),
            ('11', 'Suggested Retail Rates'),
            ('19', 'Letter Center'),
            ('20', 'Air Service Center'),
            ], 'Pickup Type'),
        'ups_packaging_type': fields.many2one('shipping.package.type', 'Packaging Type')
    }

    def _get_sale_account(self, cr, uid, context=None):
        if context is None:
            context = {}
        logsitic_obj = self.pool.get('logistic.company')
        user_rec = self.pool.get('res.users').browse(cr , uid, uid, context)
        logis_company = logsitic_obj.search(cr, uid, [])
        if not logis_company:
            return False
        return logsitic_obj.browse(cr, uid, logis_company[0], context).ship_account_id.id

    _defaults = {
        'sale_account_id': _get_sale_account,
    }

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
