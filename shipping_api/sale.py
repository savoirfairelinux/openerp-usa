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
    _inherit = 'sale.order'
    
    def _get_company_code(self, cr, user, context=None):
        return []
    
    def onchange_logis_company(self, cr, uid, ids, logistic_company_id, context=None):
        res = {}
        if logistic_company_id:
            logistic_company = self.pool.get('logistic.company').browse(cr, uid, logistic_company_id, context=context)
            res =  {'value': {'ship_company_code': logistic_company.ship_company_code,'sale_account_id':logistic_company.ship_account_id.id}}
        return res
    
    def _get_logis_company(self, cr, uid, context=None):
        if context is None:
            context = {}
        user_rec = self.pool.get('res.users').browse(cr ,uid, uid, context)
        logis_company = self.pool.get('logistic.company').search(cr, uid, [])
        return logis_company and logis_company[0] or False

    _columns= {
        'logis_company': fields.many2one('logistic.company', 'Logistic Company', help='Name of the Logistics company providing the shipper services.'),
        'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
        'rate_selection': fields.selection([('rate_card', 'Rate Card'), ('rate_request', 'Rate Request')], 'Ship Rate Method'),
        'partner_order_id': fields.many2one('res.partner', 'Ordering Contact', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="The name and address of the contact who requested the order or quotation."),
    }

    _defaults = {
        'partner_order_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['order_contact'])['order_contact'],
        'logis_company': _get_logis_company,
    }

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        addr = {}
        if part:
            addr = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context)
            addr['value'].update({'partner_order_id': part})
        return addr

sale_order()


class res_partner(osv.osv):
    _inherit = 'res.partner'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if type(ids) is not list:
            ids = [ids]
        partners = self.browse(cr, uid, ids, context=context)
        for partner in partners:
            pname = partner.name
            res.append((partner.id,pname))
        return res

res_partner()

