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
from openerp.osv import orm, fields, osv


class shipping_rate_wizard(orm.TransientModel):
    _inherit = 'shipping.rate.wizard'
    
    def _get_company_code(self, cr, user, context=None):
        return []
    
    def onchange_logis_company(self, cr, uid, ids, logistic_company_id, context=None):
        company_code = ''
        if logistic_company_id:
            logis_comp_obj =  self.pool.get('logistic.company')
            company_code = logis_comp_obj.read(cr, uid, logistic_company_id, ['ship_company_code'], context=context )['ship_company_code']
        res =  {'value': {'ship_company_code': company_code}}
        return res
    
    def _get_rate_selection(self, cr, uid, context=None):
        
        if context is None:
            context = {}
        if context.get('active_model', False) == 'sale.order':
            sale_id = context.get('active_id', False)
            if sale_id:
                sale = self.pool.get('sale.order').browse(cr, uid, sale_id, context=context)
                if sale.rate_selection:
                    return sale.rate_selection
                return sale.company_id and sale.company_id.rate_selection or 'rate_card' 
        return 'rate_card'

    def default_get(self, cr, uid, fields, context=None):
        res = super(shipping_rate_wizard, self).default_get(cr, uid, fields, context=context)
        if context is None:
            context = {}
        if context.get('active_model', False) == 'sale.order':
            sale_id = context.get('active_id', False)
            if sale_id:
                sale = self.pool.get('sale.order').browse(cr, uid, sale_id, context=context)
                res.update({
                    'logis_company': sale.logis_company and sale.logis_company.id or False,
                    'ship_company_code': sale.ship_company_code,
                    'shipping_cost': sale.shipcharge
                    })
        elif context.get('active_model', False) == 'account.invoice':
            inv_id = context.get('active_id', False)
            invoice = self.pool.get('account.invoice').browse(cr, uid, inv_id, context=context)
            if inv_id:
                res.update({
                    'shipping_cost': invoice.shipcharge
                    })
        return res

    def update_shipping_cost(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=context)
        if context is None:
            context = {}
        if context.get('active_model', False) == 'sale.order':
            sale_id = context.get('active_id', False)
            if sale_id:
                self.pool.get('sale.order').write(cr, uid, [sale_id], {'rate_selection': data.rate_selection}, context=context)
        return super(shipping_rate_wizard, self).update_shipping_cost(cr, uid, ids, context=context)

    def get_rate(self, cr, uid, ids, context=None):
        return True

    _columns= {
        'rate_selection': fields.selection([('rate_card', 'Rate Card'), ('rate_request', 'Rate Request')], 'Ship Rate Method'),
        'logis_company': fields.many2one('logistic.company', 'Shipper Company', help='Name of the Logistics company providing the shipper services.'),
        'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
        'status_message': fields.char('Status', size=128, readonly=True),
        }
    _defaults = {
        'rate_selection': _get_rate_selection,
        }

shipping_rate_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: