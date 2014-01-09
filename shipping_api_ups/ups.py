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

class ups_account_shipping(osv.osv):
    
    _name = "ups.account.shipping"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'ups_account_id': fields.many2one('ups.account', 'UPS Account', required=True),
        'accesslicensenumber': fields.related('ups_account_id', 'accesslicensenumber', type='char', size=64, string='AccessLicenseNumber', required=True),
        'userid': fields.related('ups_account_id', 'userid', type='char', size=64, string='UserId', required=True),
        'password': fields.related('ups_account_id', 'password', type='char', size=64, string='Password', required=True),
        'active': fields.related('ups_account_id', 'ups_active', string='Active', type='boolean'),
        'acc_no': fields.related('ups_account_id', 'acc_no', type='char', size=64, string='Account Number', required=True),
        'atten_name': fields.char('AttentionName', size=64, required=True, select=1),
        'tax_id_no': fields.char('Tax Identification Number', size=64 , select=1, help="Shipper's Tax Identification Number."),
        'logistic_company_id': fields.many2one('logistic.company', 'Parent Logistic Company'),
#         'ups_shipping_service_ids': fields.one2many('ups.shipping.service.type', 'ups_account_id', 'Shipping Service'),
        'ups_shipping_service_ids':fields.many2many('ups.shipping.service.type', 'shipping_service_rel', 'ups_account_id', 'service_id', 'Shipping Service'),
        'address': fields.property(
           'res.partner',
           type='many2one',
           relation='res.partner',
           string="Shipper Address",
           view_load=True),
        'trademark': fields.char('Trademark', size=1024, select=1),
        'company_id': fields.many2one('res.company', 'Company'),
    }
    _defaults = {
        'active': True
    }
    
    def onchange_ups_account(self, cr, uid, ids, ups_account_id=False, context=None):
        res = {
            'accesslicensenumber': '',
            'userid': '',
            'password': '',
            'active': True,
            'acc_no': ''
            }
        
        if ups_account_id:
            ups_account = self.pool.get('ups.account').browse(cr, uid, ups_account_id, context=context)
            res = {
                'accesslicensenumber': ups_account.accesslicensenumber,
                'userid': ups_account.userid,
                'password': ups_account.password,
                'active': ups_account.ups_active,
                'acc_no': ups_account.acc_no
                }
        return {'value': res}

ups_account_shipping()

class ups_account_shipping_service(osv.osv):
    
    _name = "ups.shipping.service.type"
    _rec_name = "description"
    
    _columns = {
        'description': fields.char('Description', size=32, required=True, select=1),
        'category': fields.char('Category', size=32, select=1),
        'shipping_service_code': fields.char('Shipping Service Code', size=8, select=1),
        'rating_service_code': fields.char('Rating Service Code', size=8, select=1),
        'ups_account_id': fields.many2one('ups.account.shipping', 'Parent Shipping Account'),
        }
    
ups_account_shipping_service()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
