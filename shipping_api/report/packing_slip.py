# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw

class report_packing_slip(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_packing_slip, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            '_get_qty': self._get_qty,
            '_get_total': self._get_total,
            '_get_count': self._get_count,
            '_get_total_packed_qty': self._get_total_packed_qty,
            '_get_package_lines': self._get_package_lines,
        })

    def _get_package_lines(self, package):
        lines = []
        line_items = {}
        done_product_ids = []
        for rec in package.stock_move_ids:
            
            line = {}
            if rec.product_id.id not in done_product_ids:
                done_product_ids.append(rec.product_id.id)
                line['id'] = rec.product_id.id
                line['code'] = rec.product_id.default_code
                line['name'] = rec.product_id.name
                line['qty'] = rec.product_qty or 0.0
                line['sale_id'] = rec.package_id.pick_id.sale_id or False
                line_items[rec.product_id.id] = line
            else:
                line_items[rec.product_id.id]['qty'] += rec.product_qty
        for line_key,line_value in line_items.items():
            lines.append(line_value)
        return lines
    
    def _get_qty(self, sale, product_id):
        qty = {}
        for line in sale.order_line:
            qty[line.product_id.id] = line.product_uom_qty
        return qty.get(product_id,0.0)

    def _get_count(self, picking, package_id):
        count = 0
        page = {}
        for package in picking.packages_ids:
            count += 1
            page[package.id] = count
        result = str(page[package_id])+ ' of ' + str(count)
        return result

    def _get_total_packed_qty(self, package):
        tot = 0.0
        for item in package.stock_move_ids:
            tot += item.product_qty
        return tot

    def _get_total(self, sale, package):
        qty = {}
        product_ids = []
        total = 0.00
        for item in package.stock_move_ids:
            product_ids.append(item.product_id.id)
        for line in sale.order_line:
            if line.product_id.id in product_ids:
                total += line.product_uom_qty
        return total

report_sxw.report_sxw(
    'report.package.packing.slip.print',
    'stock.packages',
    'addons/shipping_api/report/package_packing_slip.rml',
    parser=report_packing_slip, header=True
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: