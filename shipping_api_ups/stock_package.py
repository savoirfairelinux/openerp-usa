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

class stock_packages(osv.osv):

    def process_package(self, cr, uid, ids, context=None):
        return True

    def _get_highvalue(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            highvalue = False
            if rec.decl_val > 1000:
                highvalue = True
            res[rec.id] = highvalue
        return res

    _inherit = "stock.packages"
    _columns = {
        'shipment_digest': fields.text('ShipmentDigest'),
        'control_log_receipt': fields.binary('Control Log Receipt'),
        'highvalue': fields.function(_get_highvalue, method=True, type='boolean', string='High Value'),
        'att_file_name': fields.char('File Name',size=128),
        }

    def print_control_receipt_log(self, cr, uid, ids, context=None):
        if not ids: return []
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'control.log.receipt.print',
            'datas': {
                'model': 'stock.packages',
                'id': ids and ids[0] or False,
                'ids': ids and ids or [],
                'report_type': 'pdf'
                },
            'nodestroy': True
            }

stock_packages()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: