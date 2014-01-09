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

class account_invoice(osv.osv):
    
    _inherit = 'account.invoice'
    
    def invoice_pay_customer(self, cr, uid, ids, context=None):
        if not ids: return []
        if not context:
            context= {}
        move_line_obj = self.pool.get('account.move.line')
        voucher_line_obj = self.pool.get('account.voucher.line')
        res = super(account_invoice, self).invoice_pay_customer(cr, uid, ids, context=context)
        rec = self.browse(cr, uid, ids[0], context=context)
        move_lines = move_line_obj.search(cr, uid, [('invoice', '=', rec.id)])
        voucher_id = None
        if move_lines:
            voucher_lines = voucher_line_obj.search(cr, uid, [('move_line_id', 'in', move_lines)])
            if voucher_lines:
                for voucher_line in voucher_line_obj.browse(cr, uid, voucher_lines, context): 
                    voucher_id = voucher_line.voucher_id.id
        if voucher_id:
            res.update({'res_id': voucher_id})
        view = 'view_vendor_receipt_form'
        if rec.type in ('in_invoice','out_refund'):
            view = 'view_vendor_payment_form'
        res.update({'view_id':self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', view)[1], 'target':'current' })
        return res
    
    _columns = {
        'credit_card' : fields.boolean('Credit Card', readonly=True)
    }
    
    _defaults = {
        'credit_card' : False
    }
account_invoice()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

