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

from openerp.osv import osv, fields
from openerp.tools.translate import _

class stock_return_picking(osv.TransientModel):
    _inherit = 'stock.return.picking'
    _columns = { 
        'cc_ship_refund' : fields.boolean(string='Refund Shipcharge', required=True),
        'invoice_state': fields.selection([('2binvoiced', 'To be refunded/invoiced'), ('none', 'No invoicing'),('cc_refund','Credit Card Refund')], 'Invoicing',required=True),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        if context is None:
            context = {}
        res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        if pick:
            if 'invoice_state' in fields:
                if pick.cc_pre_auth:
                    res['invoice_state'] = 'cc_refund'
        return res

    def create_returns(self, cr, uid, ids, context=None):
        """ 
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        if context is None:
            context = {}
        
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        data_obj = self.pool.get('stock.return.picking.memory')
        voucher_obj = self.pool.get('account.voucher')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        new_picking = None
        old_policy = pick.invoice_state
        
        res = super(stock_return_picking, self).create_returns(cr, uid, ids, context)
        
        move_lines = data['product_return_moves']
        #@ Moving the refund process to On Delivery process of related incoming shipment
        if data['invoice_state'] == 'cc_refund':
            amount = 0.00
            for move in move_lines:
                return_line = data_obj.browse(cr, uid, move, context=context)
                move = move_obj.browse(cr, uid, return_line.move_id.id, context=context)
                if pick.sale_id:
                    for sale_line in pick.sale_id.order_line:
                        if sale_line.product_id and sale_line.product_id.id == move.product_id.id:
                             amount = amount + ((sale_line.price_subtotal / sale_line.product_uom_qty or 1) * return_line.quantity)
                             break

            if amount:
                voucher_ids = voucher_obj.search(cr, uid, [('rel_sale_order_id', '=', pick.sale_id.id), ('state', '=', 'posted'), ('type', '=', 'receipt'), ('cc_charge', '=', True)], order="id desc", context=context)
                if voucher_ids:
                    voucher_obj.write(cr, uid, [voucher_ids[0]], {'cc_refund_amt':amount}, context=context)
                    domain = res.get('domain') and eval(res['domain'])
                    new_pick_id = False
                    if domain and len(domain) and len(domain[0]) == 3:
                        new_pick_id = domain[0][2][0]
                    if new_pick_id:
                        self.pool.get('stock.picking').write(cr, uid, new_pick_id, {'voucher_id':voucher_ids[0]}, context=context)
        
        if old_policy == 'credit_card':
            pick_obj.write(cr, uid, [pick.id], {'invoice_state':'credit_card'}, context=context)
        return res

stock_return_picking()

class stock_picking(osv.osv):
    
    _inherit = "stock.picking"
    _columns = {
         'voucher_id' : fields.many2one('account.voucher', 'Refund Voucher', readonly=True)
    }

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        voucher_obj = self.pool.get('account.voucher')
        res = super(stock_picking, self).do_partial(cr, uid, ids, partial_datas, context=context)
        for pick in self.browse(cr, uid, ids, context=context):
            IN = OUT = False
            if pick.type == 'in':
                if pick.invoice_state == 'cc_refund' and pick.voucher_id:
                    if pick.state == 'assigned' and not pick.backorder_id.id:
                        continue
                IN = True

            if pick.type == 'out':
                rel_voucher = pick.sale_id and pick.sale_id.rel_account_voucher_id or False
                if not (pick.invoice_state == 'credit_card' and rel_voucher and pick.state == 'done'):
                    continue
                OUT = True

            if IN or OUT:
                amount = 0.00
                vch_lines = []
                Lines = pick.move_lines
                if pick.backorder_id.id and pick.state=='assigned':
                    Lines = pick.backorder_id.move_lines
                for move in Lines:
                    partial_data = partial_datas.get('move%s'%(move.id), {})
                    new_qty = partial_data.get('product_qty',0.0)
                    line = {}
                    if IN:
                        line['product_id'] = move.product_id.id
                        line['qty'] = new_qty
                        line['price_unit'] = move.product_id.list_price
                    
                    if pick.sale_id:
                        for sale_line in pick.sale_id.order_line:
                            if sale_line.product_id and sale_line.product_id.id == move.product_id.id:
                                 if IN:
                                     line['price_unit'] = sale_line.price_unit
                                 amount = amount + ((sale_line.price_subtotal / sale_line.product_uom_qty or 1) * new_qty)
                                 break
                    if IN:
                        vch_lines.append(line)

                if OUT:
                    sale = pick.sale_id
                    if sale and sale.payment_method == 'cc_pre_auth' and not sale.invoiced:
                        rel_voucher = sale.rel_account_voucher_id or False
                        if rel_voucher and rel_voucher.state != 'posted' and rel_voucher.cc_auth_code:
                            vals_vouch = {'cc_order_amt': amount,'cc_p_authorize': False, 'cc_charge': True}
                            if 'trans_type' in rel_voucher._columns.keys():
                                vals_vouch.update({'trans_type': 'PriorAuthCapture'})
                            voucher_obj.write(cr, uid, [rel_voucher.id], vals_vouch, context=context)
                            voucher_obj.authorize(cr, uid, [rel_voucher.id], context=context)
                if IN and pick.voucher_id.id:
                    context['cc_refund'] = vch_lines
                    voucher_obj.write(cr, uid, [pick.voucher_id.id], {'cc_refund_amt':amount}, context=context)
                    self.pool.get('auth.net.cc.api').do_this_transaction(cr, uid, [pick.voucher_id.id] , refund=True, context=context)
        return res
stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

   