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

class shipping_package_type(osv.osv):
    _name = 'shipping.package.type'
    _columns = {
        'name': fields.char('Package Type', size=32, required=True),
        'code': fields.char('Code', size=16),
        'length': fields.float('Length', help='Indicates the longest length of the box in inches.'),
        'width': fields.float('Width'),
        'height': fields.float('Height'),
    }

shipping_package_type()

class stock_packages(osv.osv):
    _name = "stock.packages"
    _description = "Packages of Delivery Order"
    _rec_name = "packge_no"

    def _button_visibility(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for package in self.browse(cr, uid, ids, context=context):
            result[package.id] = True
            if package.pick_id.ship_state in ['read_pick','shipped','delivered', 'draft', 'cancelled']:
                result[package.id] = False
        return result

    def _get_decl_val(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            sum = 0
            for item in rec.stock_move_ids:
                sum += item.cost or 0.0
            res[rec.id] = sum
        return res
    
    _columns = {
        'packge_no': fields.char('Package Number', size=64, help='The number of the package associated with the delivery.\
                                    Example: 3 packages may be associated with a delivery.'),
        'weight': fields.float('Weight (lbs)', required=1, help='The weight of the individual package'),
        'package_type': fields.many2one('shipping.package.type','Package Type', help='Indicates the type of package'),
        'length': fields.float('Length', help='Indicates the longest length of the box in inches.'),
        'width': fields.float('Width', help='Indicates the width of the package in inches.'),
        'height': fields.float('Height', help='Indicates the height of the package inches.'),
        'ref1': fields.selection([
            ('AJ', 'Accounts Receivable Customer Account'),
            ('AT', 'Appropriation Number'),
            ('BM', 'Bill of Lading Number'),
            ('9V', 'Collect on Delivery (COD) Number'),
            ('ON', 'Dealer Order Number'),
            ('DP', 'Department Number'),
            ('3Q', 'Food and Drug Administration (FDA) Product Code'),
            ('IK', 'Invoice Number'),
            ('MK', 'Manifest Key Number'),
            ('MJ', 'Model Number'),
            ('PM', 'Part Number'),
            ('PC', 'Production Code'),
            ('PO', 'Purchase Order Number'),
            ('RQ', 'Purchase Request Number'),
            ('RZ', 'Return Authorization Number'),
            ('SA', 'Salesperson Number'),
            ('SE', 'Serial Number'),
            ('ST', 'Store Number'),
            ('TN', 'Transaction Reference Number'),
            ('EI', 'Employee ID Number'),
            ('TJ', 'Federal Taxpayer ID No.'),
            ('SY', 'Social Security Number'),
            ], 'Reference Number 1', help='Indicates the type of 1st reference no'),
        'ref2': fields.char('Reference Number 1', size=64, help='A reference number 1 associated with the package.'),
        'ref2_code': fields.selection([
            ('AJ', 'Accounts Receivable Customer Account'),
            ('AT', 'Appropriation Number'),
            ('BM', 'Bill of Lading Number'),
            ('9V', 'Collect on Delivery (COD) Number'),
            ('ON', 'Dealer Order Number'),
            ('DP', 'Department Number'),
            ('3Q', 'Food and Drug Administration (FDA) Product Code'),
            ('IK', 'Invoice Number'),
            ('MK', 'Manifest Key Number'),
            ('MJ', 'Model Number'),
            ('PM', 'Part Number'),
            ('PC', 'Production Code'),
            ('PO', 'Purchase Order Number'),
            ('RQ', 'Purchase Request Number'),
            ('RZ', 'Return Authorization Number'),
            ('SA', 'Salesperson Number'),
            ('SE', 'Serial Number'),
            ('ST', 'Store Number'),
            ('TN', 'Transaction Reference Number'),
            ('EI', 'Employee ID Number'),
            ('TJ', 'Federal Taxpayer ID No.'),
            ('SY', 'Social Security Number'),
            ], 'Reference Number', help='Indicates the type of 2nd reference no'),
        'ref2_number': fields.char('Reference Number 2', size=64, help='A reference number 2 associated with the package.'),
        'pick_id': fields.many2one('stock.picking', 'Delivery Order'),
        'ship_move_id': fields.many2one('shipping.move', 'Delivery Order'),
        'description': fields.text('Description'),
        'logo': fields.binary('Logo'),
        'negotiated_rates': fields.float('NegotiatedRates'),
         'shipment_identific_no': fields.char('ShipmentIdentificationNumber', size=64),
         'tracking_no': fields.char('TrackingNumber', size=64),
        'ship_message': fields.text('Status Message'),
        'tracking_url': fields.char('Tracking URL', size=512),
        'package_type_id': fields.many2one('logistic.company.package.type', 'Package Type'),
        'show_button': fields.function(_button_visibility, method=True, type='boolean', string='Show'),
        #'package_item_ids' : fields.one2many('shipment.package.item','package_id','Package Items'),
        'stock_move_ids' : fields.one2many('stock.move','package_id','Package Items'),
        'decl_val': fields.function(_get_decl_val, method=True, string='Declared Value', type='float', help='The declared value of the package.')
    }

    _defaults = {
        'weight': 0.0
    }


    def print_label(self, cr, uid, ids, context=None):
        if not ids: return []
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'ship.label.print',
            'datas': {
                'model': 'stock.packages',
                'id': ids and ids[0] or False,
                'ids': ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
        }

    def print_packing_slips(self, cr, uid, ids, context=None):
        if not ids: return []
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'package.packing.slip.print',
            'datas': {
                'model': 'stock.packages',
                'id': ids and ids[0] or False,
                'ids': ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
        }

    def onchange_packge_no(self, cr, uid, ids, packge_no, line_ids, context=None):
        
        """
        Function to generate sequence on packages
        """
        ret = {}
        if packge_no:
            ret['packge_no'] = packge_no
        else:
            if line_ids:
                for line in line_ids:
                        if line and line[2] and line[2]['packge_no'] and packge_no < line[2]['packge_no']:
                            packge_no = line[2]['packge_no']
                packge_no = str(int(packge_no)+1)
            ret['packge_no'] = packge_no
        return {'value': ret}

    def onchange_weight(self, cr, uid, ids, line_ids, tot_order_weight, weight, context=None):
       
        """
        Function to automatically fill package weight
        """
        if line_ids == False:
            line_ids = []
        ret = {}
        if weight:
            ret['weight'] = weight
        else:
            used_weight = 0
            for line in line_ids:
                if line and line[2] and line[2]['weight']:
                    used_weight += line[2]['weight']
            if used_weight < tot_order_weight:
                ret['weight'] = tot_order_weight - used_weight
        return {'value': ret}

    def onchange_stock_package(self, cr, uid, ids, package_type):
        res = {}
        res['value'] = {
                'length': 0,
                'width': 0,
                'height': 0,
        }
        if package_type:
            package_type_obj = self.pool.get('shipping.package.type').browse(cr, uid, package_type)
            res['value'] = {
                'length': package_type_obj.length,
                'width':package_type_obj.width,
                'height': package_type_obj.height,
        }
        return res

stock_packages()

# TODO - Commenting the code for Package Item for future re
#class shipment_package_item(osv.osv):
#    _name = 'shipment.package.item'
#    _description = 'Shipment Package Item'
#    _rec_name = 'product_id'
#
#    def onchange_product_id(self, cr, uid, ids, product_id, qty=0.0):
#        res = {'value':{'cost':0.0}}
#        product_obj = self.pool.get('product.product')
#        if not product_id:
#            return res
#        prod = product_obj.browse(cr, uid, product_id)
#        if not qty:
#            qty = 1
#        res['value'] = {
#            'cost' : (prod.list_price * qty) or 0.0
#        }
#        return res
#
#    _columns = {
#        'product_id': fields.many2one('product.product','Product', required=True),
#        'cost': fields.float('Value', digits_compute=dp.get_precision('Account'), required=True),
#        'package_id': fields.many2one('stock.packages','Package'),
#        'qty': fields.float('Quantity', digits_compute=dp.get_precision('Account')),
#    }
#
#shipment_package_item()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: