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

import netsvc
import base64
import time
import decimal_precision as dp
from openerp.osv import fields, osv

class stock_picking(osv.osv):
    
    _inherit = "stock.picking"
    
    def onchange_logis_company(self, cr, uid, ids, logistic_company_id, context=None):
        company_code = ''
        if logistic_company_id:
            logistic_company_obj = self.pool.get('logistic.company')
            company_code = logistic_company_obj.read(cr, uid, logistic_company_id, ['ship_company_code'], context=context)['ship_company_code']
        res = {'value': {'ship_company_code': company_code}}
        return res

    def init(self, cr):
        cr.execute('alter table stock_picking alter column tot_ship_weight type numeric(16,3)')

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default['ship_state'] = 'draft'
        res = super(stock_picking, self).copy(cr, uid, id, default, context=context)
        return res

    def distribute_weight(self, cr, uid, ids, context=None):
        pack_ids_list = self.read(cr, uid, ids, ['packages_ids', 'tot_del_order_weight'], context=context)
        for pack_ids in pack_ids_list:
            if pack_ids['tot_del_order_weight'] and pack_ids['packages_ids']:
                avg_weight = pack_ids['tot_del_order_weight'] / len(pack_ids['packages_ids'])
                self.pool.get('stock.packages').write(cr, uid, pack_ids['packages_ids'], {'weight': avg_weight}, context=context)
        return True

    def _total_weight_net(self, cr, uid, ids, field_name, arg, context=None):
        """Compute the total net weight of the given Delivery order."""
        result = {}
        for pick in self.browse(cr, uid, ids, context=context):
            result[pick.id] = 0.0
            for line in pick.packages_ids:
                if line.weight:
                    result[pick.id] += line.weight
        return result

    def _total_ord_weight_net(self, cr, uid, ids, field_name, arg, context=None):
        """Compute the total net weight of the given Delivery order."""
        result = {}
        for pick in self.browse(cr, uid, ids, context=context):
            result[pick.id] = 0.0
            for line in pick.move_lines:
                if line.product_id:
                    result[pick.id] += line.product_qty * line.product_id.weight_net
        return result

    def _get_move_order(self, cr, uid, ids, context=None):
        """Get the picking ids of the given Stock Moves."""
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()

    def _get_order(self, cr, uid, ids, context=None):
        """Get the picking ids of the given Stock Packages."""
        result = {}
        for line in self.pool.get('stock.packages').browse(cr, uid, ids, context=None):
            result[line.pick_id.id] = True
        return result.keys()

    def _get_company_code(self, cr, user, context=None):
        return []
    
    _columns = {
        'logis_company': fields.many2one('logistic.company', 'Logistics Company', help='Name of the Logistics company providing the shipper services.'),
        'freight': fields.boolean('Shipment', help='Indicates if the shipment is a freight shipment.'),
        'sat_delivery': fields.boolean('Saturday Delivery', help='Indicates is it is appropriate to send delivery on Saturday.'),
        'package_type': fields.selection([
            ('01', 'Letter'),
            ('02', 'Customer Supplied Package'),
            ('03', 'Tube'),
            ('04', 'PAK'),
            ('21', 'ExpressBox'),
            ('24', '25KG Box'),
            ('25', '10KG Box'),
            ('30', 'Pallet'),
            ('2a', 'Small Express Box'),
            ('2b', 'Medium Express Box'),
            ('2c', 'Large Express Box')
            ], 'Package Type', help='Indicates the type of package'),
        'bill_shipping': fields.selection([
            ('shipper', 'Shipper'),
            ('receiver', 'Receiver'),
            ('thirdparty', 'Third Party')
            ], 'Bill Shipping to', help='Shipper, Receiver, or Third Party.'),
        'with_ret_service': fields.boolean('With Return Services', help='Include Return Shipping Information in the package.'),
        'tot_ship_weight': fields.function(_total_weight_net, method=True, type='float', digits=(16, 3), string='Total Shipment Weight',
            store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['packages_ids'], -10),
                'stock.packages': (_get_order, ['weight'], -10),
                }, help="Adds the Total Weight of all the packages in the Packages Table.",
                ),
        'tot_del_order_weight': fields.function(_total_ord_weight_net, method=True, readonly=True, string='Total Order Weight', store=False,
                                                 help="Adds the Total Weight of all the packages in the Packages Table."),
        'packages_ids': fields.one2many("stock.packages", 'pick_id', 'Packages Table'),
        'ship_state': fields.selection([
            ('draft', 'Draft'),
            ('in_process', 'In Process'),
            ('ready_pick', 'Ready for Pickup'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('void', 'Void'),
            ('hold', 'Hold'),
            ('cancelled', 'Cancelled')
            ], 'Shipping Status', readonly=True, help='The current status of the shipment'),
        'trade_mark': fields.text('Trademarks AREA'),
        'ship_message': fields.text('Message'),
        'address_validate': fields.selection([
            ('validate', 'Validate'),
            ('nonvalidate', 'No Validation')
            ], 'Address Validation', help=''' No Validation = No address validation.
                                              Validate = Fail on failed address validation.
                                              Defaults to validate. Note: Full address validation is not performed. Therefore, it is
                                              the responsibility of the Shipping Tool User to ensure the address entered is correct to
                                              avoid an address correction fee.'''),
        'ship_description': fields.text('Description'),
        'ship_from': fields.boolean('Ship From', help='Required if pickup location is different from the shipper\'s address..'),
        'ship_from_tax_id_no': fields.char('Identification Number', size=30 , select=1),
        'shipcharge': fields.float('Shipping Cost', readonly=True),
        'ship_from_address': fields.many2one('res.partner', 'Ship From Address', size=30),
#         'address': fields.many2one('res.partner', 'Ship From Address'),
        'tot_order_weight': fields.related('sale_id', 'total_weight_net', type='float', relation='sale.order', string='Total Order Weight'),
        'comm_inv': fields.boolean('Commercial Invoice'),
        'cer_orig': fields.boolean('U.S. Certificate of Origin'),
        'nafta_cer_orig': fields.boolean('NAFTA Certificate of Origin'),
        'sed': fields.boolean('Shipper Export Declaration (SED)'),
        'prod_option': fields.selection([
            ('01', 'AVAILABLE TO CUSTOMS UPON REQUEST'),
            ('02', 'SAME AS EXPORTER'),
            ('03', 'ATTACHED LIST'),
            ('04', 'UNKNOWN'),
            (' ', ' ')
            ], 'Option'),
        'prod_company': fields.char('CompanyName', size=256, help='Only applicable when producer option is empty or not present.'),
        'prod_tax_id_no': fields.char('TaxIdentificationNumber', size=256, help='Only applicable when producer option is empty or not present.'),
        'prod_address_id': fields.many2one('res.partner', 'Producer Address', help='Only applicable when producer option is empty or not present.'),
        'inv_option': fields.selection([
            ('01', 'Unknown'),
            ('02', 'Various'),
            (' ', ' ')
            ], 'Sold to Option'),
        'inv_company': fields.char('CompanyName', size=256, help='Only applicable when Sold to option is empty or not present.'),
        'inv_tax_id_no': fields.char('TaxIdentificationNumber', size=256, help='Only applicable when Sold to option is empty or not present.'),
        'inv_att_name': fields.char('AttentionName', size=256, help='Only applicable when Sold to option is empty or not present.'),
        'inv_address_id': fields.many2one('res.partner', 'Sold To Address', help='Only applicable when Sold to option is empty or not present.'),
        'blanket_begin_date': fields.date('Blanket Begin Date'),
        'blanket_end_date': fields.date('Blanket End Date'),
        'comm_code': fields.char('Commodity Code', size=256,),
        'exp_carrier': fields.char('ExportingCarrier', size=256),
        'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
        'ship_charge': fields.float('Value', digits_compute=dp.get_precision('Account'))
    }

    _defaults = {
        'address_validate': 'nonvalidate',
        'comm_inv': False,
        'cer_orig': False,
        'nafta_cer_orig': False,
        'sed': False,
        'ship_state' : 'draft',
        'bill_shipping': 'shipper',
        'ship_charge': 0.0
    }
    
    
    def process_ship(self, cr, uid, ids, context=None):
        return True

    def print_labels(self, cr, uid, ids, context=None):
        if not ids: return []
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'multiple.label.print',
            'datas': {
                'model': 'stock.picking',
                'id': ids and ids[0] or False,
                'ids': ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
        }

    def print_packing_slips(self, cr, uid, ids, context=None):
        if not ids: return []
        packages_ids = []
        for package in self.browse(cr, uid, ids[0]).packages_ids:
            packages_ids.append(package.id)
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'package.packing.slip.print',
            'datas': {
                'model': 'stock.packages',
                'id': ids and ids[0] or False,
                'ids': packages_ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
        }

    def process_void(self, cr, uid, ids, context=None):
        return True

    def cancel_ship(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'ship_state': 'cancelled'}, context=context)
        return True

    def _get_account_analytic_invoice(self, cursor, user, picking, move_line):
        partner_id = picking.partner_id and picking.partner_id.id or False
        analytic_obj = self.pool.get('account.analytic.default')
        rec = analytic_obj.account_get(cursor, user, move_line.product_id.id, partner_id, user, time.strftime('%Y-%m-%d'), context={})
        if rec:
            return rec.analytic_id.id
        return super(stock_picking, self)._get_account_analytic_invoice(cursor, user, picking, move_line)

    def send_conf_mail(self, cr, uid, ids, context=None):
        for id in ids:
            obj = self.browse(cr, uid, id)
            if obj and obj.address_id and obj.address_id.email:
                email_temp_obj = self.pool.get('email.template')
                template_id = email_temp_obj.search(cr, uid, [('object_name.model', '=', 'stock.picking'), ('ship_mail', '=', True)], context=context)
                if template_id:
                    template_obj_list = email_temp_obj.browse(cr, uid, template_id)
                    for template_obj in template_obj_list:
                        subj = self.get_value(obj, template_obj, 'def_subject') or ''
                        vals = {
                          'email_to': self.get_value(cr, uid, obj, template_obj.def_to, context) or '',
                          'body_text': self.get_value(cr, uid, obj, template_obj.def_body_text) or '',
                          'body_html': self.get_value(cr, uid, obj, template_obj.def_body_html) or '',
                          'account_id': template_obj.from_account.id,
                          'folder': 'outbox',
                          'state': 'na',
                          'subject': self.get_value(cr, uid, obj, template_obj.def_subject) or '',
                          'email_cc': self.get_value(cr, uid, obj, template_obj.def_cc) or '',
                          'email_bcc': self.get_value(cr, uid, obj, template_obj.def_bcc) or '',
                          'email_from': template_obj.from_account.email_id or '',
                          'reply_to': self.get_value(cr, uid, obj, template_obj.reply_to) or '' ,
                          'date_mail': time.strftime('%Y-%m-%d %H:%M:%S'),
                          }
                        if vals['email_to'] and vals['account_id']:
                            mail_id = self.pool.get('email_template.mailbox').create(cr, uid, vals, context=context)
                            data = {}
                            data['model'] = 'stock.picking'
                            if template_obj.report_template:
                                reportname = 'report.' + self.pool.get('ir.actions.report.xml').read(cr, uid, template_obj.report_template.id,
                                                                                                     ['report_name'], context=context)['report_name']
                                service = netsvc.LocalService(reportname)
                                (result, format) = service.create(cr, uid, [id], data, context=context)
                                email_temp_obj._add_attachment(cr, uid, mail_id, subj, base64.b64encode(result),
                                                               template_obj.file_name or 'Order.pdf', context=context)
        return True

stock_picking()

class stock_picking_out(osv.osv):
    
    _inherit = "stock.picking.out"
    
    def _total_weight_net(self, cr, uid, ids, field_name, arg, context=None):
        return self.pool.get('stock.picking')._total_weight_net(cr, uid, ids, field_name, arg, context)
    
    def _get_order(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking')._get_order(cr, uid, ids, context)
    
    def _total_ord_weight_net(self, cr, uid, ids, field_name, arg, context=None):
        return self.pool.get('stock.picking')._total_ord_weight_net(cr, uid, ids, field_name, arg, context)
    
    def _get_company_code(self, cr, user, context=None):
        return self.pool.get('stock.picking')._get_company_code(cr, user, context)
    
    def onchange_logis_company(self, cr, uid, ids, logistic_company_id, context=None):
        return self.pool.get('stock.picking').onchange_logis_company(cr, uid, ids, logistic_company_id, context)
    
    def distribute_weight(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').distribute_weight(cr, uid, ids, context)
    
    def process_ship(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').process_ship(cr, uid, ids, context)
    
    
    _columns = {
        'logis_company': fields.many2one('logistic.company', 'Shipper Company', help='Name of the Logistics company providing the shipper services.'),
        'freight': fields.boolean('Shipment', help='Indicates if the shipment is a freight shipment.'),
        'sat_delivery': fields.boolean('Saturday Delivery', help='Indicates is it is appropriate to send delivery on Saturday.'),
        'package_type': fields.selection([
            ('01', 'Letter'),
            ('02', 'Customer Supplied Package'),
            ('03', 'Tube'),
            ('04', 'PAK'),
            ('21', 'ExpressBox'),
            ('24', '25KG Box'),
            ('25', '10KG Box'),
            ('30', 'Pallet'),
            ('2a', 'Small Express Box'),
            ('2b', 'Medium Express Box'),
            ('2c', 'Large Express Box')
            ], 'Package Type', help='Indicates the type of package'),
        'bill_shipping': fields.selection([
            ('shipper', 'Shipper'),
            ('receiver', 'Receiver'),
            ('thirdparty', 'Third Party')
            ], 'Bill Shipping to', help='Shipper, Receiver, or Third Party.'),
        'with_ret_service': fields.boolean('With Return Services', help='Include Return Shipping Information in the package.'),
        'tot_ship_weight': fields.function(_total_weight_net, method=True, type='float', digits=(16, 3), string='Shipment Weight',
            store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['packages_ids'], -10),
                'stock.packages': (_get_order, ['weight'], -10),
                }, help="Adds the Total Weight of all the packages in the Packages Table.",
                ),
        'tot_del_order_weight': fields.function(_total_ord_weight_net, method=True, readonly=True, string='Total Order Weight', store=False,
                                                 help="Adds the Total Weight of all the packages in the Packages Table."),
        'packages_ids': fields.one2many("stock.packages", 'pick_id', 'Packages Table'),
        'shipcharge': fields.float('Shipping Cost', readonly=True),
        'ship_state': fields.selection([
            ('draft', 'Draft'),
            ('in_process', 'In Process'),
            ('ready_pick', 'Ready for Pickup'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('void', 'Void'),
            ('hold', 'Hold'),
            ('cancelled', 'Cancelled')
            ], 'Shipping Status', readonly=True, help='The current status of the shipment'),
        'trade_mark': fields.text('Trademarks AREA'),
        'ship_message': fields.text('Message'),
        'address_validate': fields.selection([
            ('validate', 'Validate'),
            ('nonvalidate', 'No Validation')
            ], 'Address Validation', help=''' No Validation = No address validation.
                                              Validate = Fail on failed address validation.
                                              Defaults to validate. Note: Full address validation is not performed. Therefore, it is
                                              the responsibility of the Shipping Tool User to ensure the address entered is correct to
                                              avoid an address correction fee.'''),
        'ship_description': fields.text('Description'),
        'ship_from': fields.boolean('Ship From', help='Required if pickup location is different from the shipper\'s address..'),
        'ship_from_tax_id_no': fields.char('Identification Number', size=64 , select=1),
        'ship_from_address': fields.many2one('res.partner', 'Ship From Address'),
#         'address': fields.many2one('res.partner', 'Ship From Address'),
        'tot_order_weight': fields.related('sale_id', 'total_weight_net', type='float', relation='sale.order', string='Total Order Weight'),
        'comm_inv': fields.boolean('Commercial Invoice'),
        'cer_orig': fields.boolean('U.S. Certificate of Origin'),
        'nafta_cer_orig': fields.boolean('NAFTA Certificate of Origin'),
        'sed': fields.boolean('Shipper Export Declaration (SED)'),
        'prod_option': fields.selection([
            ('01', 'AVAILABLE TO CUSTOMS UPON REQUEST'),
            ('02', 'SAME AS EXPORTER'),
            ('03', 'ATTACHED LIST'),
            ('04', 'UNKNOWN'),
            (' ', ' ')
            ], 'Option'),
        'prod_company': fields.char('CompanyName', size=256, help='Only applicable when producer option is empty or not present.'),
        'prod_tax_id_no': fields.char('TaxIdentificationNumber', size=256, help='Only applicable when producer option is empty or not present.'),
        'prod_address_id': fields.many2one('res.partner', 'Producer Address', help='Only applicable when producer option is empty or not present.'),
        'inv_option': fields.selection([
            ('01', 'Unknown'),
            ('02', 'Various'),
            (' ', ' ')
            ], 'Sold to Option'),
        'inv_company': fields.char('CompanyName', size=256, help='Only applicable when Sold to option is empty or not present.'),
        'inv_tax_id_no': fields.char('TaxIdentificationNumber', size=256, help='Only applicable when Sold to option is empty or not present.'),
        'inv_att_name': fields.char('AttentionName', size=256, help='Only applicable when Sold to option is empty or not present.'),
        'inv_address_id': fields.many2one('res.partner', 'Sold To Address', help='Only applicable when Sold to option is empty or not present.'),
        'blanket_begin_date': fields.date('Blanket Begin Date'),
        'blanket_end_date': fields.date('Blanket End Date'),
        'comm_code': fields.char('Commodity Code', size=256,),
        'exp_carrier': fields.char('ExportingCarrier', size=256),
        'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
        'ship_charge': fields.float('Value', digits_compute=dp.get_precision('Account'))
    }

    _defaults = {
        'address_validate': 'nonvalidate',
        'comm_inv': False,
        'cer_orig': False,
        'nafta_cer_orig': False,
        'sed': False,
        'ship_state' : 'draft',
        'bill_shipping': 'shipper',
        'ship_charge': 0.0
    }

    def print_labels(self, cr, uid, ids, context=None):
        if not ids: return []
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'multiple.label.print',
            'datas': {
                'model': 'stock.picking',
                'id': ids and ids[0] or False,
                'ids': ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
        }
    
    def print_packing_slips(self, cr, uid, ids, context=None):
        if not ids: return []
        packages_ids = []
        for package in self.browse(cr, uid, ids[0]).packages_ids:
            packages_ids.append(package.id)
        x = {
            'type': 'ir.actions.report.xml',
            'report_name': 'package.packing.slip.print',
            'datas': {
                'model': 'stock.packages',
                'id': ids and ids[0] or False,
                'ids': packages_ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
        }
        return x
    

stock_picking_out()

# class stock_partial_picking(osv.osv_memory):
#     
#     _inherit = "stock.partial.picking"
# 
#     def do_partial(self, cr, uid, ids, context=None):
#         ret = super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
#         pick_obj = self.pool.get('stock.picking')
#         if context is None:
#             context = {}
#         picking_ids = context.get('active_ids', False)
#         new_pick_ids = []
#         for pick in pick_obj.browse(cr, uid, picking_ids, context=context):
#             if pick.backorder_id:
#                 new_pick_ids.append(pick.backorder_id.id)
#         try:
#             if new_pick_ids:
#                 model_obj = self.pool.get('ir.model.data')
#                 view_obj = self.pool.get('ir.ui.view')
#                 model_id = model_obj._get_id(cr, uid, 'stock', 'view_picking_out_form')
#                 view_id = model_obj.read(cr, uid, [model_id], ['res_id'])[0]['res_id']
#                 domain = "[('id', 'in', [" + ','.join(map(str, new_pick_ids)) + "])]"
#                 result = {
#                     "type": "ir.actions.act_window",
#                     "res_model": "stock.picking",
#                     "view_type": "form",
#                     "view_mode": "tree,form",
#                     "name": "Delivery Order",
#                     "domain": domain,
#                     "context": {'search_default_available': 0},
#                     'views': [(False, 'tree'), (view_id, 'form')]
#                     }
#                 return result
#         except Exception, e:
#             logger = netsvc.Logger()
#             logger.notifyChannel("Warning", netsvc.LOG_WARNING,
#                     "Issue with opening the processed delivery order. %s." % e)
#             return ret
# 
#         return ret
# 
# stock_partial_picking()

class stock_move(osv.osv):
    _inherit = "stock.move"

    _columns = {
        'package_id' : fields.many2one('stock.packages', help='Indicates the package', string='Package'),
        'cost': fields.float('Value', digits_compute=dp.get_precision('Account'))
    }
    
    def onchange_quantity(self, cr, uid, ids, product_id, product_qty, product_uom, product_uos, location_id=False, sale_line_id=False):
        result = super(stock_move, self).onchange_quantity(cr, uid, ids, product_id, product_qty, product_uom, product_uos)
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            if sale_line_id:
                sale_unit_price = self.pool.get('sale.order.line').browse(cr, uid, sale_line_id).price_unit
                price = sale_unit_price * product_qty
            else:
                price = product.list_price * product_qty
            result['value'].update({'cost': price})
        return result
    
stock_move()

class Prod(osv.osv):
    _inherit = 'product.product'
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if context is None:
            context = {}

        if context.get('move_type', 'p') == 'package' and context.get('move_ids'):
            picks = self.pool.get('stock.packages').browse(cr, uid, context.get('move_ids')).pick_id
            if picks:
                p_ids = [x.product_id.id for x in picks.move_lines]
                args += [('id', 'in', p_ids)]

        return super(Prod, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)
Prod()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
