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

import re

from openerp.osv import fields, osv

class logistic_company(osv.osv):
    _inherit="logistic.company"

    def _get_company_code(self, cr, user, context=None):
        res =  super(logistic_company, self)._get_company_code(cr, user, context=context)
        res.append(('ups', 'UPS'))
        return res

    _columns = {
        'ship_company_code': fields.selection(_get_company_code, 'Logistic Company', method=True, required=True, size=64),
        'ship_req_web': fields.char('Ship Request Website', size=256 ),
        'ship_req_port': fields.integer('Ship Request Port'),
        'ship_req_test_web': fields.char('Test Ship Request Website', size=256 ),
        'ship_req_test_port': fields.integer('Test Ship Request Port'),
        'ship_accpt_web': fields.char('Ship Accept Website', size=256 ),
        'ship_accpt_port': fields.integer('Ship Accept Port' ),
        'ship_accpt_test_web': fields.char('Test Ship Accept Website', size=256),
        'ship_accpt_test_port': fields.integer('Test Ship Accept Port'),
        'ship_void_web': fields.char('Ship Void Website', size=256),
        'ship_void_port': fields.integer('Ship Void Port'),
        'ship_void_test_web': fields.char('Test Ship Void Website', size=256),
        'ship_void_test_port': fields.integer('Test Ship Void Port'),
        'ship_tracking_url': fields.char('Tracking URL', size=256),
        'ups_shipping_account_ids': fields.one2many('ups.account.shipping', 'logistic_company_id', 'Shipping Account'),
        }

    def onchange_shipping_number(self, cr, uid, ids, shipping_no, url, context=None):
        ret = {}
        if url:
            b = url[url.rindex('/'): len(url)]
            b = b.strip('/')
            if re.match("^[0-9]*$", b):
                url = url[0:url.rindex('/')]
            url += ('/' + shipping_no)
            ret['url'] = url
        return{'value': ret}

logistic_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: