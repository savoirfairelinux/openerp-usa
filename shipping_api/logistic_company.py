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

class logistic_company(osv.osv):
    _name = "logistic.company"
    
    def _get_company_code(self, cr, user, context=None):
        return []
    
    _columns = {
        'name': fields.char('Name', size=32, required=True, select=1),
        'ship_company_code': fields.selection(_get_company_code, 'Logistic Company', method=True,size=64),
        'url': fields.char('Website',size=256 , select=1),
        'company_id': fields.many2one('res.company', 'Company'),
        'test_mode': fields.boolean('Test Mode'),
        'ship_account_id': fields.property(
           'account.account',
           type='many2one',
           relation='account.account',
           string="Ship Account",
           view_load=True),
        'note': fields.text('Notes'),
    }

logistic_company()

class logistic_company_service_type(osv.osv):
    _name = "logistic.company.service.type"
    _columns = {
        'name': fields.char('Service Name', size=32, required=True),
        'logistic_company_id': fields.many2one('logistic.company', 'Logistic Company'),
        'code': fields.char('Service Code', size=32),
        'description': fields.char('Description', size=128),
    }

logistic_company_service_type()

class logistic_company_package_type(osv.osv):
    
    _name = "logistic.company.package.type"
    
    _columns = {
        'name': fields.char('Package Name', size=32, required=True),
        'logistic_company_id': fields.many2one('logistic.company', 'Logistic Company'),
        'code': fields.char('Package Code', size=32),
        'description': fields.char('Description', size=128),
    }

logistic_company_package_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
