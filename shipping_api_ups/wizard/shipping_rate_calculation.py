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

import xml2dic

from openerp.osv import orm, fields, osv
from openerp.tools.translate import _

class shipping_rate_wizard(orm.TransientModel):
    _inherit = 'shipping.rate.wizard'

    def _get_company_code(self, cr, user, context=None):
        res = super(shipping_rate_wizard, self)._get_company_code(cr, user, context=context)
        res.append(('ups', 'UPS'))
        return res

    def default_get(self, cr, uid, fields, context=None):
        res = super(shipping_rate_wizard, self).default_get(cr, uid, fields, context=context)
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        if context.get('active_model', False) == 'sale.order':
            sale_id = context.get('active_id', False)
            sale = sale_obj.browse(cr, uid, sale_id, context=context)
            if sale_id:
                res.update({
                    'ups_shipper_id': sale.ups_shipper_id and sale.ups_shipper_id.id or False,
                    'ups_service_id': sale.ups_service_id and sale.ups_service_id.id or False,
                    'ups_pickup_type': sale.ups_pickup_type,
                    'ups_packaging_type': sale.ups_packaging_type and sale.ups_packaging_type.id or False,
                    'partner_id': sale.partner_id and sale.partner_id.id or False,
                    'partner_shipping_id': sale.partner_shipping_id and sale.partner_shipping_id.id or False
                    })
        elif context.get('active_model', False) == 'account.invoice':
            inv_id = context.get('active_id', False)
            invoice = self.pool.get('account.invoice').browse(cr, uid, inv_id, context=context)
            sale_ids = sale_obj.search(cr, uid, [('invoice_ids','in', [inv_id])], context=context)
            sale_id = sale_ids and sale_ids[0] or False
            sale = sale_id and sale_obj.browse(cr, uid, sale_id, context=context)
            shipping_id = sale_id and sale.partner_shipping_id and sale.partner_shipping_id.id or False
            if not shipping_id:
                addr_obj = self.pool.get('res.partner')
                address_ids = addr_obj.search(cr, uid, [('id', '=', invoice.partner_id.id)], context=context)
                shipping_id = address_ids and address_ids[0] or False
            if inv_id:
                res.update({
                    'partner_id': invoice.partner_id and invoice.partner_id.id or False,
                    'partner_shipping_id': shipping_id
                    })
        return res

    def update_shipping_cost(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=context)
        if context is None:
            context = {}
        if not (data['rate_selection'] == 'rate_request' and data['ship_company_code'] == 'ups'):
            return super(shipping_rate_wizard, self).update_shipping_cost(cr, uid, ids, context=context)
        
        if context.get('active_model',False) == 'sale.order':
            sale_id = context.get('active_id', False)
            sale_obj = self.pool.get('sale.order')
            if sale_id:
                sale_obj.write(cr , uid, [sale_id], {
                    'shipcharge': data.shipping_cost,
                    'ship_method': data.ups_service_id and data.ups_service_id.description or '',
                    'sale_account_id': data.logis_company and data.logis_company.ship_account_id and data.logis_company.ship_account_id.id or False,
                    'ship_company_code': data.ship_company_code,
                    'logis_company': data.logis_company and data.logis_company.id or False,
                    'ups_shipper_id': data.ups_shipper_id and data.ups_shipper_id.id or False,
                    'ups_service_id': data.ups_service_id and data.ups_service_id.id or False,
                    'ups_pickup_type': data.ups_pickup_type,
                    'ups_packaging_type': data.ups_packaging_type and data.ups_packaging_type.id or False,
                    'rate_selection': data.rate_selection
                    }, context=context)
            sale_obj.button_dummy(cr, uid, [sale_id], context=context)
            return {'nodestroy': False, 'type': 'ir.actions.act_window_close'}
        elif context.get('active_model',False) == 'account.invoice':
            inv_id = context.get('active_id', False)
            
            inv_obj = self.pool.get('account.invoice')
            if inv_id:
                inv_obj.write(cr , uid, [inv_id], {
                    'shipcharge': data.shipping_cost,
                    'ship_method': data.ups_service_id and data.ups_service_id.description or '',
                    }, context=context)
                return {'nodestroy': False, 'type': 'ir.actions.act_window_close'}
        return True

    def get_rate(self, cr, uid, ids, context=None):
        sale_obj = self.pool.get('sale.order')
        data = self.browse(cr, uid, ids[0], context=context)
        sale_obj.write(cr,uid,context.get('active_ids'),{'ups_shipper_id':data.ups_shipper_id.id,
                                                         'ups_service_id':data.ups_service_id.id,
                                                         'ups_pickup_type':data.ups_pickup_type,
                                                         'ups_packaging_type':data.ups_packaging_type.id},context=context)
        if context is None:
            context = {}
        if not (data['rate_selection'] == 'rate_request' and data['ship_company_code'] == 'ups'):
            return super(shipping_rate_wizard, self).get_rate(cr, uid, ids, context)
#        if context.get('active_model', False) == 'sale.order':
        if context.get('active_model', False) in ['sale.order', 'account.invoice'] and 'active_id' in context:
            if context['active_model'] == 'sale.order':
                sale = sale_obj.browse(cr, uid, context['active_id'], context=context)
                weight = sale.total_weight_net or 0.00
            elif context['active_model'] == 'account.invoice':
                invoice = self.pool.get('account.invoice').browse(cr, uid, context['active_id'], context=context)
                weight = invoice.total_weight_net or 0.00
            receipient_zip = data.partner_shipping_id and data.partner_shipping_id.zip or ''
            receipient_country_code = data.partner_shipping_id.country_id and data.partner_shipping_id.country_id.code or ''
            access_license_no = data.ups_shipper_id and  data.ups_shipper_id.accesslicensenumber or ''
            user_id = data.ups_shipper_id and  data.ups_shipper_id.userid or ''
            password = data.ups_shipper_id and data.ups_shipper_id.password or ''
            pickup_type_ups = data.ups_pickup_type
            shipper_zip = data.ups_shipper_id and data.ups_shipper_id.address and data.ups_shipper_id.address.zip or ''
            shipper_country_code =  data.ups_shipper_id and data.ups_shipper_id.address and  data.ups_shipper_id.address.country_id and \
                                    data.ups_shipper_id.address.country_id.code or ''
            ups_info_shipper_no = data.ups_shipper_id and data.ups_shipper_id.acc_no or ''
            service_type_ups = data.ups_service_id and data.ups_service_id.shipping_service_code or ''
            packaging_type_ups = data.ups_packaging_type.code
            test_mode = False
            test_mode = data.logis_company and data.logis_company.test_mode or True
            url = 'https://wwwcie.ups.com/ups.app/xml/Rate' or 'https://onlinetools.ups.com/ups.app/xml/Rate'
            rate_request = """<?xml version=\"1.0\"?>
            <AccessRequest xml:lang=\"en-US\">
                <AccessLicenseNumber>%s</AccessLicenseNumber>
                <UserId>%s</UserId>
                <Password>%s</Password>
            </AccessRequest>
            <?xml version=\"1.0\"?>
            <RatingServiceSelectionRequest xml:lang=\"en-US\">
                <Request>
                    <TransactionReference>
                        <CustomerContext>Rating and Service</CustomerContext>
                        <XpciVersion>1.0001</XpciVersion>
                    </TransactionReference>
                    <RequestAction>Rate</RequestAction>
                    <RequestOption>Rate</RequestOption>
                </Request>
            <PickupType>
                <Code>%s</Code>
            </PickupType>
            <Shipment>
                <Shipper>
                    <Address>
                        <PostalCode>%s</PostalCode>
                        <CountryCode>%s</CountryCode>
                    </Address>
                <ShipperNumber>%s</ShipperNumber>
                </Shipper>
                <ShipTo>
                    <Address>
                        <PostalCode>%s</PostalCode>
                        <CountryCode>%s</CountryCode>
                    <ResidentialAddressIndicator/>
                    </Address>
                </ShipTo>
                <ShipFrom>
                    <Address>
                        <PostalCode>%s</PostalCode>
                        <CountryCode>%s</CountryCode>
                    </Address>
                </ShipFrom>
                <Service>
                    <Code>%s</Code>
                </Service>
                <Package>
                    <PackagingType>
                        <Code>%s</Code>
                    </PackagingType>
                    <PackageWeight>
                        <UnitOfMeasurement>
                            <Code>LBS</Code>
                        </UnitOfMeasurement>
                        <Weight>%s</Weight>
                    </PackageWeight>
                </Package>
            </Shipment>
            </RatingServiceSelectionRequest>""" % (access_license_no, user_id, password, pickup_type_ups, shipper_zip,shipper_country_code, 
                                                   ups_info_shipper_no,receipient_zip, receipient_country_code, shipper_zip, shipper_country_code, 
                                                   service_type_ups, packaging_type_ups, weight)
            try:
                from urllib2 import Request, urlopen, URLError, quote
                request = Request(url, rate_request)
                response_text = urlopen(request).read()
                response_dic = xml2dic.main(response_text)
                str_error = ''
                for response in response_dic['RatingServiceSelectionResponse'][0]['Response']:
                    if response.get('Error'):
                        for item in response['Error']:
                            if item.get('ErrorDescription'):
                                str_error = item['ErrorDescription']
                                self.write(cr, uid, [data.id], {'status_message': "Error : " + item['ErrorDescription'] })
                if not str_error:
                    for response in response_dic['RatingServiceSelectionResponse'][1]['RatedShipment']:
                        if response.get('TotalCharges'):
                            amount = response['TotalCharges'][1]['MonetaryValue']
                            sale_obj.write(cr, uid, context.get('active_ids'), {'shipcharge': amount or 0.00, 'status_message': 'Success!'},context=context)
                    return True

            except URLError, e:
                if hasattr(e, 'reason'):
                    print 'Could not reach the server, reason: %s' % e.reason
                elif hasattr(e, 'code'):
                    print 'Could not fulfill the request, code: %d' % e.code
                raise
        mod, modid = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'shipping_api_ups', 'view_for_shipping_rate_wizard_shipping')
        return {
            'name':_("Get Rate"),
            'view_mode': 'form',
            'view_id': modid,
            'view_type': 'form',
            'res_model': 'shipping.rate.wizard',
            'type': 'ir.actions.act_window',
            'target':'new',
            'nodestroy': True,
            'domain': '[]',
            'res_id': ids[0],
            'context':context,
        }

    
    def onchage_shipping_service(self, cr, uid, ids, ups_shipper_id=False, context=None):
         vals = {}
         service_type_ids = []
         if ups_shipper_id:
             shipper_obj = self.pool.get('ups.account.shipping').browse(cr, uid, ups_shipper_id)
             for shipper in shipper_obj.ups_shipping_service_ids:
                 service_type_ids.append(shipper.id)
         domain = [('id', 'in', service_type_ids)]
         return {'domain': {'ups_service_id': domain}}
    
    _columns= {
        'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
        'ups_shipper_id': fields.many2one('ups.account.shipping', 'Shipper'),
        'ups_service_id': fields.many2one('ups.shipping.service.type', 'Shipping Service'),
        'ups_pickup_type': fields.selection([
            ('01', 'Daily Pickup'),
            ('03', 'Customer Counter'),
            ('06', 'One Time Pickup'),
            ('07', 'On Call Air'),
            ('11', 'Suggested Retail Rates'),
            ('19', 'Letter Center'),
            ('20', 'Air Service Center'),
        ], 'Pickup Type'),
        'ups_packaging_type': fields.many2one('shipping.package.type','Packaging Type'),
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'partner_shipping_id': fields.many2one('res.partner', 'Shipping Address'),
        }
shipping_rate_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
