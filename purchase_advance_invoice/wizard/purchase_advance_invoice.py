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
from openerp.osv import osv, fields
from openerp.tools.translate import _


class purchase_advance_invoice(osv.osv_memory):
    _name = "purchase.advance.invoice"
    _description = "Purchase Advance Invoice"
    _columns = {
        'product_id': fields.many2one('product.product', 'Advance Product', required=True,
                                      help="Select a product of type service which is called 'Advance Product'. You may have to create it and set it as a default value on this field."),
        'amount': fields.float('Advance Amount', digits=(16, 2), required=True,
                               help="The amount to be invoiced in advance."),
        'qtty': fields.float('Quantity', digits=(16, 2), required=True,
                             help='The quantity of product to be invoiced in advance'),
    }
    _defaults = {
        'qtty': 1.0
    }

    def create_invoices(self, cr, uid, ids, context=None):
        """
             To create advance invoice

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs if we want more than one
             @param context: A standard dictionary

             @return:

        """
        invoice_list = []
        po_obj = self.pool.get('purchase.order')
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_obj = self.pool.get('account.invoice')
        addr_obj = self.pool.get('res.partner')
        journal_obj = self.pool.get('account.journal')
        if context is None:
            context = {}

        for purchase_adv_obj in self.browse(cr, uid, ids, context=context):
            for purchase_order in po_obj.browse(cr, uid, context.get('active_ids', []), context=context):
                inv_line_ids = []
                invoice_ids = []
                val = inv_line_obj.product_id_change(cr, uid, [], purchase_adv_obj.product_id.id,
                        uom_id=False, partner_id=purchase_order.partner_id.id, fposition_id=purchase_order.fiscal_position.id)
                line_id = inv_line_obj.create(cr, uid, {
                    'name': val['value']['name'],
                    'account_id': val['value']['account_id'],
                    'price_unit': purchase_adv_obj.amount,
                    'quantity': purchase_adv_obj.qtty,
                    'discount': False,
                    'uos_id': val['value']['uos_id'],
                    'product_id': purchase_adv_obj.product_id.id,
                    'invoice_line_tax_id': [(6, 0, val['value']['invoice_line_tax_id'])],
                })
                inv_line_ids.append(line_id)
                addr = addr_obj.address_get(cr, uid, [purchase_order.partner_id.id], ['invoice'])
                journal_ids = journal_obj.search(cr, uid, [('type', '=', 'purchase')])
                context.update({'type':'in_invoice','journal_type':'purchase'})
                inv_vals = {
                    'name': purchase_order.partner_ref or purchase_order.name,
                    'origin': purchase_order.name,
                    'type': 'in_invoice',
                    'reference': False,
                    'account_id': purchase_order.partner_id.property_account_payable.id,
                    'journal_id':journal_ids and journal_ids[0] or False,
                    'partner_id': purchase_order.partner_id.id,
                    'address_invoice_id': addr['invoice'],
                    'invoice_line': [(6, 0, inv_line_ids)],
                    'currency_id': purchase_order.pricelist_id.currency_id.id,
                    'comment': '',
                    'fiscal_position': purchase_order.fiscal_position.id or purchase_order.partner_id.property_account_position.id
                }

                inv_id = inv_obj.create(cr, uid, inv_vals, context=context)
                inv_obj.button_reset_taxes(cr, uid, [inv_id], context=context)
                for invoice in purchase_order.invoice_ids:
                    invoice_ids.append(invoice.id)
                invoice_ids.append(inv_id)
                po_obj.write(cr, uid, purchase_order.id, {'invoice_ids': [(6, 0, invoice_ids)]})
                invoice_list.append(inv_id)

        if purchase_order.invoice_method in ('picking','order'):
            self.pool.get('purchase.order.line').create(cr, uid, {
                'order_id': purchase_order.id,
                'name': val['value']['name'],
                'date_planned':purchase_order.date_order,
                'price_unit': -purchase_adv_obj.amount,
                'product_uom_qty': purchase_adv_obj.qtty,
                'product_uos': val['value']['uos_id'],
                'product_uom': val['value']['uos_id'],
                'product_id': purchase_adv_obj.product_id.id,
                'discount': False,
                'taxes_id': [(6, 0, val['value']['invoice_line_tax_id'])],
            }, context=context)


        context.update({'invoice_id':invoice_list})
        return {
            'name': 'Open Invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.open.invoice',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

purchase_advance_invoice()

class purchase_open_invoice(osv.osv_memory):
    _name = "purchase.open.invoice"
    _description = "Purchase Open Invoice"

    def open_invoice(self, cr, uid, ids, context=None):

        """
             To open the advance invoice.
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs if we want more than one
             @param context: A standard dictionary
             @return:

        """
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        for advance_pay in self.browse(cr, uid, ids, context=context):
            form_res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
            form_id = form_res and form_res[1] or False
            tree_res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_tree')
            tree_id = tree_res and tree_res[1] or False
            
        return {
            'name': _('Advance Invoice'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'account.invoice',
            'res_id': int(context['invoice_id'][0]),
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'context': context,
            'type': 'ir.actions.act_window',
         }

purchase_open_invoice()
