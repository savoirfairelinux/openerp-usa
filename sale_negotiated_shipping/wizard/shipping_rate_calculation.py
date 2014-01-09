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

from osv import orm, fields, osv

class shipping_rate_wizard(orm.TransientModel):
    _name = "shipping.rate.wizard"
    _description = "Calculates shipping charges"
    _columns = {
        'shipping_cost': fields.float('Shipping Cost'),
        'account_id': fields.many2one('account.account', 'Account'),
        'rate_select': fields.many2one('shipping.rate.config', 'Shipping Method'),
        }

    def update_shipping_cost(self, cr, uid, ids, context=None):
        """
        Function to update sale order and invoice with new shipping cost and method
        """
        datas = self.browse(cr, uid, ids[0], context=context)
        if context is None:
            context = {}
        if context.get('active_model', False) in ['sale.order', 'account.invoice'] and 'active_id' in context:
            model = context['active_model']
            model_obj = self.pool.get(model)
            model_id = context.get('active_id', False)
            if model_id:
                model_obj.write(cr, uid, [model_id], {
                    'shipcharge': datas.shipping_cost,
                    'ship_method': datas.rate_select.shipmethodname,
                    'sale_account_id': datas.account_id.id,
                    'ship_method_id': datas.rate_select.id,
                    }, context=context)
            if model == 'sale.order':
                model_obj.button_dummy(cr, uid, [model_id], context=context)
            if model == 'account.invoice':
                model_obj.button_reset_taxes(cr, uid, [model_id], context=context)
            return {'nodestroy': False, 'type': 'ir.actions.act_window_close'}

    def onchange_shipping_method(self, cr, uid, ids, rate_config_id, context=None):
        ret = {}
        if context is None:
            context = {}
        rate_config_obj = self.pool.get('shipping.rate.config')
        rate_obj = self.pool.get('shipping.rate')
        if context.get('active_model', False) in ['sale.order', 'account.invoice'] and 'active_id' in context:
            cost = 0.0 
            rate_config = rate_config_obj.browse(cr, uid, rate_config_id, context=context)
            account_id = rate_config.account_id and rate_config.account_id.id or False
            model = context['active_model']
            model_obj = self.pool.get(model).browse(cr, uid, context['active_id'], context=context)
            cr.execute('select type,id from res_partner where company_id = %s', (tuple([model_obj.company_id.id])))
            res = cr.fetchall()
            address = dict(res)
            if address:
                address_id = address.get('delivery', False) or address.get('default', False) or\
                             address.values() and address.values()[0]
                address_obj = self.pool.get('res.partner').browse(cr, uid, address_id, context=context)
                if address_obj:
                    cost = rate_obj.find_cost(cr, uid, rate_config_id, address_obj, model_obj, context=context)
            ret = {'value': {'shipping_cost': cost, 'account_id': account_id}}
        return ret

shipping_rate_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: