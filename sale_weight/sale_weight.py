# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009 Numérigraphe SARL.
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""Compute the net weight of sale orders."""
from openerp.osv import osv, fields
class sale_order(osv.osv):
    """Add the total net weight to the object "Sale Order"."""
    
    _inherit = "sale.order"

    def _total_weight_net(self, cr, uid, ids, field_name, arg, context):
       
        """Compute the total net weight of the given Sale Orders."""
        result = {}
        print "field name, arg", field_name, arg
        for sale in self.browse(cr, uid, ids, context=context):
            result[sale.id] = 0.0
            for line in sale.order_line:
                if line.product_id:
                    result[sale.id] += line.weight_net or 0.0
        return result

    def _get_order(self, cr, uid, ids, context={}):
        """Get the order ids of the given Sale Order Lines."""
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids,
            context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'total_weight_net': fields.function(_total_weight_net, method=True,
            readonly=True, string='Total Weight',
            help="The cumulated net weight of all the order lines.",
            store={
                # Low priority to compute this before fields in other modules
                'sale.order': (lambda self, cr, uid, ids, c={}: ids,
                     ['order_line'], -10),
                'sale.order.line': (_get_order,
                     ['product_uom_qty', 'product_id'], -10),
            },
        ),
    }

# Record the net weight of the order line
class sale_order_line(osv.osv):
    """Add the net weight to the object "Sale Order Line"."""
    _inherit = 'sale.order.line'

    def _weight_net(self, cr, uid, ids, field_name, arg, context):
       
        """Compute the net weight of the given Sale Order Lines."""
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = 0.0

            if line.product_id:
                
                if line.product_id.weight_net:
                    result[line.id] += (line.product_id.weight_net
                        * line.product_uom_qty / line.product_uom.factor)
                else:
                    result[line.id] += (line.th_weight
                        * line.product_uom_qty / line.product_uom.factor)
        
        return result

    _columns = {
#         'weight_net':fields.function(_weight_net, string='Net Weight'),
        'weight_net': fields.function(_weight_net, method=True,
            readonly=True, string='Net Weight', help="The net weight",
            store={
                # Low priority to compute this before fields in other modules
               'sale.order.line': (lambda self, cr, uid, ids, c={}: ids,
                   ['product_uom_qty', 'product_id'], -11),
            },
        ),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
