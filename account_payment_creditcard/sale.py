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
from tools.translate import _
import netsvc

class sale_order(osv.osv):
    _inherit = "sale.order"

#     def onchange_partner_id(self, cr, uid, ids, part_id, context={}):
#         result = super(sale_order, self).onchange_partner_id(cr, uid, ids, part_id).get('value', {})
#         if part_id:
#             result.update({'payment_method':'cc_pre_auth', 'order_policy':'credit_card'})#Default values for the shiping policy
#         return {'value': result}
    
    def on_change_payment_method(self, cr, uid, ids, payment_method, order, part):
        order_policy = order
        if payment_method:
            if payment_method == 'invoice':
                order_policy = 'picking'
            elif payment_method == 'cc_pre_auth':
                    order_policy = 'credit_card'
        return {'value': {'order_policy':order_policy}}
    
    def pay(self, cr, uid, ids, context=None):
        '''
        Display Pay invoice form when clicking on Pay button from sale order
        '''
        wf_service = netsvc.LocalService("workflow")
        invoice_id = False
        so = self.browse(cr, uid, ids[0], context=context)
        for invoice in so.invoice_ids:
            if invoice.state != 'open':
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
            invoice_id = invoice.id
        
        if not invoice_id:
            raise osv.except_osv(_('Warning!'),_('No invoice has been created!'))
        if not ids: return []
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        self.pool.get('account.invoice').write(cr, uid, invoice_id, {'credit_card': True}, context=context)
        
        ctx = {
                'invoice_type':'out_invoice',
                'type': 'receipt',
                'sale_id':ids[0]
        }
        ret_dict = {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': ctx
                    
        }
        voucher_ids = self.pool.get('account.voucher').search(cr, uid, [('rel_sale_order_id','=',so.id),('state','not in',['cancel','posted'])], context=context)
        if voucher_ids:
            ret_dict.update(
                  {
                   'res_id' : voucher_ids[0],
                   })
        else:
            ctx.update({
                'default_partner_id': so.partner_id.id,
                'default_amount': so.amount_total,
                'default_name':so.name,
                'close_after_process': True,
                'default_rel_sale_order_id': so.id,
                'default_cc_order_amt': so.amount_total,
                'default_cc_order_date': so.date_order,
                'default_type':'receipt',
                'default_journal_id':user.company_id.cc_journal_id and user.company_id.cc_journal_id.id or False,
                'default_invoice_id':invoice_id,
                })
            ret_dict.update(
                  {
                   'context' : ctx
                   })
        return ret_dict

    def _invoiced_search(self, cursor, user, obj, name, args, context=None):
        if not len(args):
            return []
        clause = ''
        sale_clause = ''
        no_invoiced = False
        for arg in args:
            if arg[1] == '=':
                if arg[2]:
                    clause += 'AND inv.state = \'paid\''
                else:
                    clause += 'AND inv.state != \'cancel\' AND sale.state != \'cancel\'  AND inv.state <> \'paid\'  AND rel.order_id = sale.id '
                    sale_clause = ',  sale_order AS sale '
                    no_invoiced = True

        cursor.execute('SELECT rel.order_id ' \
                'FROM sale_order_invoice_rel AS rel, account_invoice AS inv ' + sale_clause + \
                'WHERE rel.invoice_id = inv.id ' + clause)
        res = cursor.fetchall()
        if no_invoiced:
            cursor.execute('SELECT sale.id ' \
                    'FROM sale_order AS sale ' \
                    'WHERE sale.id NOT IN ' \
                        '(SELECT rel.order_id ' \
                        'FROM sale_order_invoice_rel AS rel) and sale.state != \'cancel\'')
            res.extend(cursor.fetchall())
        if not res:
            return [('id', '=', 0)]
        return [('id', 'in', [x[0] for x in res])]

    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        '''
        Update pay boolean field on sale order if creditcard payment is done
        '''
        ret = super(sale_order, self)._invoiced(cursor, user, ids, name, arg, context=context)
        for key, value in ret.items():
            if not value:
                so = self.browse(cursor, user, key, context=context)
                if so.order_policy == 'credit_card' and so.rel_account_voucher_id:
                    if so.rel_account_voucher_id.state == 'posted':
                        ret[key] = True
        return ret
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)
        cr.commit()
        for sale_obj in self.browse(cr, uid, ids, context=context):
            if sale_obj.shipped and sale_obj.invoiced and sale_obj.state != 'done':
                sale_obj.write({'state':'done'})
        return res
    
    def _get_invoice(self, cr, uid, ids, context=None):
        return self.pool.get('sale.order').search(cr, uid, [('invoice_ids', 'in', ids)], context=context)

    def _get_voucher(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.voucher').browse(cr, uid, ids, context=context):
            if line.rel_sale_order_id:
                result[line.rel_sale_order_id.id] = True
        return result.keys()
    
    _columns = {

        'payment_method':fields.selection([('cc_pre_auth', 'Credit Card – PreAuthorized'),
                                           ('invoice', 'Invoice'),
                                           ('cod', 'COD'),
                                           ('p_i_a', 'Pay In Advance'), ], 'Payment Method'),
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice On Order After Delivery'),
            ('picking', 'Invoice From The Picking'),
            ('credit_card', 'CC Pre-Auth Pick Charge Ship'),
         ], 'Order Policy', required=True, readonly=True, states={'draft': [('readonly', False)]},
         help="""The Order Policy is used to synchronise invoice and delivery operations.
  - The 'Pay Before delivery' choice will first generate the invoice and then generate the picking order after the payment of this invoice.
  - The 'Shipping & Manual Invoice' will create the picking order directly and wait for the user to manually click on the 'Invoice' button to generate the draft invoice.
  - The 'Invoice On Order After Delivery' choice will generate the draft invoice based on sales order after all picking lists have been finished.
  - The 'Invoice From The Picking' choice is used to create an invoice during the picking process."""),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('cc_auth', 'Draft Authorized'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('shipping_except', 'Shipping Exception'),
            ('done', 'Done')
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
        'cc_pre_auth':fields.boolean('Creditcard Pre-authorised'),
        'rel_account_voucher_id':fields.many2one('account.voucher', 'Related Payment'),
        'invoiced': fields.function(_invoiced, method=True, string='Paid',
        type='boolean', help="It indicates that an invoice has been paid.",
        store={
                 'account.invoice'  : (_get_invoice, ['state'], 20),
                 'sale.order'       : (lambda self, cr, uid, ids, c={}: ids, ['state'], 20),
                 'account.voucher'  : (_get_voucher, ['state'], 20),
                 }),
        'cc_ship_refund' : fields.boolean('Ship Refunded', readonly=True),
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        default = default.copy()
        default['rel_account_voucher_id'] = False
        default['cc_pre_auth'] = False
        default['cc_ship_refund'] = False
        return super(sale_order, self).copy(cr, uid, id, default, context=context)
    
    _defaults = {
          'cc_ship_refund': lambda * a : False,
          'payment_method': lambda * a: 'cc_pre_auth'
    }
    
    def action_ship_create(self, cr, uid, ids, context=None):
        ret = super(sale_order, self).action_ship_create(cr, uid, ids, context=context)
        for sale_obj in self.browse(cr, uid, ids, context=context):
            if sale_obj.order_policy == 'credit_card':
                for pick in sale_obj.picking_ids:
                    self.pool.get('stock.picking.out').write(cr, uid, [pick.id], {'invoice_state': 'credit_card'}, context=context)
        return ret
sale_order()
