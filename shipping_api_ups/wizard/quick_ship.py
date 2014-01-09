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

from xml.dom.minidom import Document
import httplib
import xml2dic
import base64
import tempfile
import Image
from urlparse import urlparse

from openerp.osv import orm, fields, osv
from openerp.tools.translate import _

class quick_ship(orm.TransientModel):
    _name = "quick.ship"
    _description = "Quick Ship"
    _rec_name = 'saleorder_id'
    _columns = {
        'ship_log_id': fields.many2one('shipping.move', 'Ship Move'),
        'saleorder_id': fields.many2one('sale.order', 'Sale Order', required='1'),
        'sender': fields.many2one('res.partner', 'Sender'),
        'send_addr': fields.many2one('res.partner', 'Sender Address'),
        'recipient': fields.many2one('res.partner', 'Recipient'),
        'address_id': fields.many2one('res.partner', 'Address', help="Ship to address"),
        'quantum_view': fields.boolean('Send QuantumView Notifications'),
        'ups_shipper_id': fields.many2one('ups.account.shipping', 'Bill to'),
        'logis_company': fields.many2one('logistic.company', 'Shipper Company', help='Name of the Logistics company providing the shipper services.'),
        'ups_service_id': fields.many2one('ups.shipping.service.type', 'Shipping Service', help='The specific UPS Service offered'),
        'ups_packaging_type': fields.many2one('shipping.package.type','Package Type',help='Indicates the type of package – taken from \
                                        Package Type on the Shipment or can be overridden here on individual package.'),
        'length': fields.float('Length', help='Indicates the longest length of the box in inches.'),
        'width': fields.float('Width'),
        'height': fields.float('Height'),
        'weight': fields.float('Weight (lbs)'),
        'insured_val': fields.float('Insured Value'),
        'addn_service': fields.boolean('Additional Service Options'),
        'description': fields.char('Description', size=256,),
        'inv_no': fields.char('Invoice Number', size=64,),
        'ref_no': fields.char('Reference Number', size=64,),
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
            ('EI', 'Employer ID Number'),
            ('TJ', 'Federal Taxpayer ID No.'),
            ('SY', 'Social Security Number')
            ], 'Reference Code', help='Indicates the type of package'),
        'shipcharge': fields.float('Rate'),
        'sat_delivery': fields.boolean('Saturday Delivery', help='Indicates is it is appropriate to send delivery on Saturday.'),
        'verbal_confirm': fields.boolean('Verbal Confirmation of Delivery'),
        'con_name': fields.char('Name', size=128,),
        'con_phone': fields.char('Phone', size=64,),
        'cod': fields.boolean('Collect on Delivery (COD)'),
        'amount': fields.float('Amount'),
        'acc_cash_moneyorder': fields.boolean('Accept Cashier Check/Money Order Only'),
        'shipper_release': fields.boolean('Shipper Release'),
        'deliv_conf': fields.boolean('Delivery Confirmation'),
        'dc_opt': fields.selection([('', ''), ('', '')], 'DC Options'),
        'deliv_conf': fields.boolean('Offset the Climate Impact of This Shipment', help="UPS Carbon Neutral"),
        'addnl_handling': fields.boolean('Additional Handling'),
        'response': fields.text('Response'),
        'logo':fields.binary('Logo')
        }

    def onchange_sale_id(self, cr, uid, ids, saleorder_id, context=None):
        ret = {}
        if saleorder_id:
            sale = self.pool.get('sale.order').browse(cr, uid, saleorder_id, context=context)
            ret.update({
                'recipient': sale.partner_id.id,
                'address_id': sale.partner_shipping_id.id,
                'sender':sale.partner_id.id,
                'send_addr':sale.partner_shipping_id.id,
                'logis_company':sale.logis_company.id,
                'ups_service_id':sale.ups_service_id.id,
                'ups_packaging_type':sale.ups_packaging_type.id,
                'ups_shipper_id':sale.ups_shipper_id.id
                })
            service_type_obj = self.pool.get('ups.shipping.service.type')
            ups_shipping_service_ids = service_type_obj.search(cr, uid, [('description', 'like', sale.ship_method)], context=context)
            if ups_shipping_service_ids:
                ups_shipping_service = service_type_obj.browse(cr, uid, ups_shipping_service_ids, context=context)[0]
                ret['service'] = ups_shipping_service.id
        return {'value':ret}

    def fill_addr(self, addr_id):
        ret = {
            'AddressLine1': addr_id and addr_id.street or '',
            'AddressLine2': addr_id and addr_id.street2 or '',
            'AddressLine3': "",
            'City': addr_id and addr_id.city or '',
            'StateProvinceCode': addr_id and addr_id.state_id.id and addr_id.state_id.code or '',
            'PostalCode': addr_id and addr_id.zip or '',
            'CountryCode': addr_id and addr_id.country_id.id and addr_id.country_id.code or '',
            'ResidentialAddress': "",
            'PostalCode': addr_id and addr_id.zip or '',
            }
        return ret

    def get_package(self, quick_ship_id):
        if not quick_ship_id:
            return []
        ret = []
        ret.append({
            'Description': quick_ship_id.description or "",
            'PackagingType': {
                 'Code': quick_ship_id.ups_packaging_type.code or "",
                 'Description': quick_ship_id.ups_packaging_type.name},#PackagingType
            'Dimensions': {
                'UnitOfMeasurement': {'Code': "IN", 'Description': "Inches"},
                'Length': str(quick_ship_id.length or "0"),
                'Width': str(quick_ship_id.width or "0"),
                'Height': str(quick_ship_id.height or "0")
                },#Dimensions
            'PackageWeight': {
                'UnitOfMeasurement': {'Code': "LBS", 'Description': "Pounds"},
                'Weight': str(quick_ship_id.weight or "0")
                },#'LargePackageIndicator':"",
            'ReferenceNumber': {'BarCodeIndicator': "", 'Code': quick_ship_id.ref1 or "", 'Value': ""},
            'AdditionalHandling': "",
            })
        return ret

    def process_ship(self, cr, uid, ids, context=None):
        quick_ship_id = self.browse(cr, uid, ids[0], context=context)
        data_for_Access_Request = {
            'AccessLicenseNumber': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.accesslicensenumber or '',
            'UserId': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.userid or '',
            'Password': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.password or ''
            }
        data_for_confirm_request = { 
            'ShipmentConfirmRequest': {
                'Request': {
                    'RequestAction': "ShipConfirm",
                    'RequestOption': "nonvalidate",
                    'TransactionReference': {'CustomerContext': "",},#---------optional data
                    },#Request
                'Shipment': {
                    'Description': quick_ship_id.description or "Shipping",
                    'ReturnService': {'Code': "8", 'DocumentsOnly':"" },
                    'Shipper': {
                        'Name': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.name or "",
                        'AttentionName': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.atten_name or "",
                        'ShipperNumber': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.acc_no or "",
                        'TaxIdentificationNumber': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.tax_id_no or "",
                        'PhoneNumber': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.address and quick_ship_id.ups_shipper_id.address.phone or "",
                        'FaxNumber': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.address and quick_ship_id.ups_shipper_id.address.fax or "",
                        'EMailAddress': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.address and quick_ship_id.ups_shipper_id.address.email or "",
                        'Address': self.fill_addr(quick_ship_id.ups_shipper_id and quick_ship_id.ups_shipper_id.address or '')
                        },#Shipper
                    'ShipTo': {
                        'CompanyName': quick_ship_id.address_id and quick_ship_id.address_id.name or '',
                        'AttentionName': "",
                        'TaxIdentificationNumber': "",
                        'PhoneNumber': "",
                        'FaxNumber': quick_ship_id.address_id.id and quick_ship_id.address_id.fax or '',
                        'EMailAddress': quick_ship_id.address_id.id and quick_ship_id.address_id.email or '',
                        'Address': self.fill_addr(quick_ship_id.address_id.id and quick_ship_id.address_id),
                        'LocationID': "",
                        },#ShipTo
                    'ShipFrom': {
                        'CompanyName': quick_ship_id.send_addr.company_id and quick_ship_id.send_addr.company_id.name or '',
                        'AttentionName': quick_ship_id.send_addr.name or "",
                        'TaxIdentificationNumber': '',
                        'PhoneNumber': quick_ship_id.send_addr.id and quick_ship_id.send_addr.phone or '',
                        'FaxNumber': quick_ship_id.send_addr.id and quick_ship_id.send_addr.fax or '',
                        'Address': self.fill_addr(quick_ship_id.send_addr.id and quick_ship_id.send_addr or ''),
                        },
                    'PaymentInformation': {
                        'Prepaid': {
                            'BillShipper': {'AccountNumber': quick_ship_id.ups_shipper_id and quick_ship_id.ups_shipper_id.acc_no or ""},#BillShipper
                            },#Prepaid
                        },#PaymentInformation,
                    'GoodsNotInFreeCirculationIndicator': "",
                    'RateInformation': {'NegotiatedRatesIndicator': ""},#RateInformation
                    'Service': {
                        'Code': quick_ship_id.ups_service_id.id and str(quick_ship_id.ups_service_id.shipping_service_code) or "",
                        'Description': quick_ship_id.ups_service_id.id and quick_ship_id.ups_service_id.description or ""},#Service
                    'InvoiceLineTotal': {'CurrencyCode': "", 'MonetaryValue': str(quick_ship_id.amount) or ""},#InvoiceLineTotal
                    'Package': self.get_package(quick_ship_id)
                    },#Shipment
                'LabelSpecification': {
                    'LabelPrintMethod': {'Code': "GIF", 'Description': "GIF"},
                    'HTTPUserAgent': "",
                    'LabelStockSize': {'Height': "4", 'Width': "6"},
                    'LabelImageFormat': {'Code': "GIF", 'Description': "GIF"},
                    },#LabelSpecification
                },#ShipmentConfirmRequest
            }
        doc1 = Document()
        AccessRequest = doc1.createElement("AccessRequest")
        AccessRequest.setAttribute("xml:lang", "en-US")
        doc1.appendChild(AccessRequest)

        AccessLicenseNumber = doc1.createElement("AccessLicenseNumber")
        ptext = doc1.createTextNode(data_for_Access_Request["AccessLicenseNumber"])
        AccessLicenseNumber.appendChild(ptext)
        AccessRequest.appendChild(AccessLicenseNumber)

        UserId = doc1.createElement("UserId")
        ptext = doc1.createTextNode(data_for_Access_Request["UserId"])
        UserId.appendChild(ptext)
        AccessRequest.appendChild(UserId)

        Password = doc1.createElement("Password")
        ptext = doc1.createTextNode(data_for_Access_Request["Password"])
        Password.appendChild(ptext)
        AccessRequest.appendChild(Password)

        Request_string1 = doc1.toprettyxml()

        ######SECOND PART

        Package_count = 0#max value =200
        doc2 = Document()

        ShipmentConfirmRequest = doc2.createElement("ShipmentConfirmRequest")
        doc2.appendChild(ShipmentConfirmRequest)

        Request = doc2.createElement("Request")
        ShipmentConfirmRequest.appendChild(Request)

        RequestAction = doc2.createElement("RequestAction")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Request"]["RequestAction"])
        RequestAction.appendChild(ptext)
        Request.appendChild(RequestAction)

        RequestOption = doc2.createElement("RequestOption")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Request"]["RequestOption"])
        RequestOption.appendChild(ptext)
        Request.appendChild(RequestOption)

        TransactionReference = doc2.createElement("TransactionReference")
        Request.appendChild(TransactionReference)

        CustomerContext = doc2.createElement("CustomerContext")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Request"]["TransactionReference"]['CustomerContext'])
        CustomerContext.appendChild(ptext)
        TransactionReference.appendChild(CustomerContext)

        Shipment = doc2.createElement("Shipment")
        ShipmentConfirmRequest.appendChild(Shipment)

        Description = doc2.createElement("Description")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Description"])
        Description.appendChild(ptext)
        Shipment.appendChild(Description)
        if 0:#quick_ship_id.with_ret_service:
            ReturnService = doc2.createElement("ReturnService")
            Shipment.appendChild(ReturnService)
            Code = doc2.createElement("Code")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ReturnService"]["Code"])
            Code.appendChild(ptext)
            ReturnService.appendChild(Code)

        Shipper = doc2.createElement("Shipper")
        Shipment.appendChild(Shipper)

        Name = doc2.createElement("Name")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["Name"])
        Name.appendChild(ptext)
        Shipper.appendChild(Name)

        AttentionName = doc2.createElement("AttentionName")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["AttentionName"])
        AttentionName.appendChild(ptext)
        Shipper.appendChild(AttentionName)

        ShipperNumber = doc2.createElement("ShipperNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["ShipperNumber"])
        ShipperNumber.appendChild(ptext)
        Shipper.appendChild(ShipperNumber)

        TaxIdentificationNumber = doc2.createElement("TaxIdentificationNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["TaxIdentificationNumber"])
        TaxIdentificationNumber.appendChild(ptext)
        Shipper.appendChild(TaxIdentificationNumber)
        PhoneNumber = doc2.createElement("PhoneNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["PhoneNumber"])
        PhoneNumber.appendChild(ptext)
        Shipper.appendChild(PhoneNumber)

        FaxNumber = doc2.createElement("FaxNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["FaxNumber"])
        FaxNumber.appendChild(ptext)
        Shipper.appendChild(FaxNumber)

        EMailAddress = doc2.createElement("EMailAddress")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["EMailAddress"])
        EMailAddress.appendChild(ptext)
        Shipper.appendChild(EMailAddress)

        # Address
        Address = doc2.createElement("Address")
        Shipper.appendChild(Address)

        AddressLine1 = doc2.createElement("AddressLine1")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["Address"]["AddressLine1"])
        AddressLine1.appendChild(ptext)
        Address.appendChild(AddressLine1)

        AddressLine2 = doc2.createElement("AddressLine2")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["Address"]["AddressLine2"])
        AddressLine2.appendChild(ptext)
        Address.appendChild(AddressLine2)

        AddressLine3 = doc2.createElement("AddressLine3")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["Address"]["AddressLine3"])
        AddressLine3.appendChild(ptext)
        Address.appendChild(AddressLine3)

        City = doc2.createElement("City")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["Address"]["City"])
        City.appendChild(ptext)
        Address.appendChild(City)

        StateProvinceCode = doc2.createElement("StateProvinceCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["Address"]["StateProvinceCode"])
        StateProvinceCode.appendChild(ptext)
        Address.appendChild(StateProvinceCode)

        PostalCode = doc2.createElement("PostalCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["Address"]["PostalCode"])
        PostalCode.appendChild(ptext)
        Address.appendChild(PostalCode)
        
        CountryCode = doc2.createElement("CountryCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Shipper"]["Address"]["CountryCode"])
        CountryCode.appendChild(ptext)
        Address.appendChild(CountryCode)
        
        ShipTo = doc2.createElement("ShipTo")
        Shipment.appendChild(ShipTo)
        CompanyName = doc2.createElement("CompanyName")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["CompanyName"])
        CompanyName.appendChild(ptext)
        ShipTo.appendChild(CompanyName)

        AttentionName = doc2.createElement("AttentionName")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["AttentionName"])
        AttentionName.appendChild(ptext)
        ShipTo.appendChild(AttentionName)

        TaxIdentificationNumber = doc2.createElement("TaxIdentificationNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["TaxIdentificationNumber"])
        TaxIdentificationNumber.appendChild(ptext)
        ShipTo.appendChild(TaxIdentificationNumber)

        PhoneNumber = doc2.createElement("PhoneNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["PhoneNumber"])
        PhoneNumber.appendChild(ptext)
        ShipTo.appendChild(PhoneNumber)

        FaxNumber = doc2.createElement("FaxNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["FaxNumber"])
        FaxNumber.appendChild(ptext)
        ShipTo.appendChild(FaxNumber)

        EMailAddress = doc2.createElement("EMailAddress")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["EMailAddress"])
        EMailAddress.appendChild(ptext)
        ShipTo.appendChild(EMailAddress)

        LocationID = doc2.createElement("LocationID")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["LocationID"])
        LocationID.appendChild(ptext)
        ShipTo.appendChild(LocationID)

        Address = doc2.createElement("Address")
        ShipTo.appendChild(Address)
        AddressLine1 = doc2.createElement("AddressLine1")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["Address"]["AddressLine1"])
        AddressLine1.appendChild(ptext)
        Address.appendChild(AddressLine1)

        AddressLine2 = doc2.createElement("AddressLine2")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["Address"]["AddressLine2"])
        AddressLine2.appendChild(ptext)
        Address.appendChild(AddressLine2)

        AddressLine2 = doc2.createElement("AddressLine3")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["Address"]["AddressLine3"])
        AddressLine3.appendChild(ptext)
        Address.appendChild(AddressLine3)

        City = doc2.createElement("City")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["Address"]["City"])
        City.appendChild(ptext)
        Address.appendChild(City)

        StateProvinceCode = doc2.createElement("StateProvinceCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["Address"]["StateProvinceCode"])
        StateProvinceCode.appendChild(ptext)
        Address.appendChild(StateProvinceCode)

        PostalCode = doc2.createElement("PostalCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["Address"]["PostalCode"])
        PostalCode.appendChild(ptext)
        Address.appendChild(PostalCode)

        CountryCode = doc2.createElement("CountryCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipTo"]["Address"]["CountryCode"])
        CountryCode.appendChild(ptext)
        Address.appendChild(CountryCode)

        ShipFrom = doc2.createElement("ShipFrom")
        Shipment.appendChild(ShipFrom)
        CompanyName = doc2.createElement("CompanyName")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["CompanyName"])
        CompanyName.appendChild(ptext)
        ShipFrom.appendChild(CompanyName)

        AttentionName = doc2.createElement("AttentionName")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["AttentionName"])
        AttentionName.appendChild(ptext)
        ShipFrom.appendChild(AttentionName)

        TaxIdentificationNumber = doc2.createElement("TaxIdentificationNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["TaxIdentificationNumber"])
        TaxIdentificationNumber.appendChild(ptext)
        ShipFrom.appendChild(TaxIdentificationNumber)

        PhoneNumber = doc2.createElement("PhoneNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["PhoneNumber"])
        PhoneNumber.appendChild(ptext)
        ShipFrom.appendChild(PhoneNumber)

        FaxNumber = doc2.createElement("FaxNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["FaxNumber"])
        FaxNumber.appendChild(ptext)
        ShipFrom.appendChild(FaxNumber)

        Address = doc2.createElement("Address")
        ShipFrom.appendChild(Address)
        AddressLine1 = doc2.createElement("AddressLine1")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["Address"]["AddressLine1"])
        AddressLine1.appendChild(ptext)
        Address.appendChild(AddressLine1)

        AddressLine2 = doc2.createElement("AddressLine2")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["Address"]["AddressLine2"])
        AddressLine2.appendChild(ptext)
        Address.appendChild(AddressLine2)

        AddressLine3 = doc2.createElement("AddressLine3")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["Address"]["AddressLine3"])
        AddressLine3.appendChild(ptext)
        Address.appendChild(AddressLine3)

        City = doc2.createElement("City")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["Address"]["City"])
        City.appendChild(ptext)
        Address.appendChild(City)

        StateProvinceCode = doc2.createElement("StateProvinceCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["Address"]["StateProvinceCode"])
        StateProvinceCode.appendChild(ptext)
        Address.appendChild(StateProvinceCode)
        PostalCode = doc2.createElement("PostalCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["Address"]["PostalCode"])
        PostalCode.appendChild(ptext)
        Address.appendChild(PostalCode)

        CountryCode = doc2.createElement("CountryCode")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["ShipFrom"]["Address"]["CountryCode"])
        CountryCode.appendChild(ptext)
        Address.appendChild(CountryCode)

        PaymentInformation = doc2.createElement("PaymentInformation")
        Shipment.appendChild(PaymentInformation)
        Prepaid = doc2.createElement("Prepaid")
        PaymentInformation.appendChild(Prepaid)

        BillShipper = doc2.createElement("BillShipper")
        Prepaid.appendChild(BillShipper)

        AccountNumber = doc2.createElement("AccountNumber")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["PaymentInformation"]["Prepaid"]\
                                                            ["BillShipper"]["AccountNumber"])
        AccountNumber.appendChild(ptext)
        BillShipper.appendChild(AccountNumber)

        GoodsNotInFreeCirculationIndicator = doc2.createElement("GoodsNotInFreeCirculationIndicator")
        Shipment.appendChild(GoodsNotInFreeCirculationIndicator)

        RateInformation = doc2.createElement("RateInformation")
        Shipment.appendChild(RateInformation)
        NegotiatedRatesIndicator = doc2.createElement("NegotiatedRatesIndicator")
        RateInformation.appendChild(NegotiatedRatesIndicator)

        Service = doc2.createElement("Service")
        Shipment.appendChild(Service)
        Code = doc2.createElement("Code")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Service"]["Code"])
        Code.appendChild(ptext)
        Service.appendChild(Code)
        Description = doc2.createElement("Description")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Service"]["Description"])
        Description.appendChild(ptext)
        Service.appendChild(Description)

        if (quick_ship_id.send_addr.id and quick_ship_id.send_addr.country_id.code == 'US') and  quick_ship_id.address_id.id and \
            quick_ship_id.address_id.country_id.code in ('PR', 'CA'):
            InvoiceLineTotal = doc2.createElement("InvoiceLineTotal")
            Shipment.appendChild(InvoiceLineTotal)

            MonetaryValue = doc2.createElement("MonetaryValue")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["InvoiceLineTotal"]["MonetaryValue"])
            MonetaryValue.appendChild(ptext)
            InvoiceLineTotal.appendChild(MonetaryValue)

        Package_count = len(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"])
        for i in range(0,Package_count):
            Package = doc2.createElement("Package")
            Shipment.appendChild(Package)

            Description = doc2.createElement("Description")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["Description"])
            Description.appendChild(ptext)
            Package.appendChild(Description)
            PackagingType = doc2.createElement("PackagingType")
            Package.appendChild(PackagingType)

            Code = doc2.createElement("Code")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["PackagingType"]["Code"])
            Code.appendChild(ptext)
            PackagingType.appendChild(Code)
#             Description = doc2.createElement("Description")
# #             ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["PackagingType"]["Description"])
#             Description.appendChild(ptext)
#             PackagingType.appendChild(Description)

            Dimensions = doc2.createElement("Dimensions")
            Package.appendChild(Dimensions)

            Length = doc2.createElement("Length")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["Dimensions"]["Length"])
            Length.appendChild(ptext)
            Dimensions.appendChild(Length)
            Width = doc2.createElement("Width")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["Dimensions"]["Width"])
            Width.appendChild(ptext)
            Dimensions.appendChild(Width)
            Height = doc2.createElement("Height")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["Dimensions"]["Height"])
            Height.appendChild(ptext)
            Dimensions.appendChild(Height)
            UnitOfMeasurement = doc2.createElement("UnitOfMeasurement")
            Dimensions.appendChild(UnitOfMeasurement)

            Code = doc2.createElement("Code")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["Dimensions"]\
                                                                ['UnitOfMeasurement']["Code"])
            Code.appendChild(ptext)
            UnitOfMeasurement.appendChild(Code)
            Description = doc2.createElement("Description")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["Dimensions"]\
                                                                ['UnitOfMeasurement']["Description"])
            Description.appendChild(ptext)
            UnitOfMeasurement.appendChild(Description)

            PackageWeight = doc2.createElement("PackageWeight")
            Package.appendChild(PackageWeight)

            UnitOfMeasurement = doc2.createElement("UnitOfMeasurement")
            PackageWeight.appendChild(UnitOfMeasurement)
            Code = doc2.createElement("Code")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]['PackageWeight']\
                                                                ['UnitOfMeasurement']["Code"])
            Code.appendChild(ptext)
            UnitOfMeasurement.appendChild(Code)

            Description = doc2.createElement("Description")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]['PackageWeight']\
                                                                ['UnitOfMeasurement']["Description"])
            Description.appendChild(ptext)
            UnitOfMeasurement.appendChild(Description)

            Weight = doc2.createElement("Weight")
            ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]['PackageWeight']["Weight"])
            Weight.appendChild(ptext)
            PackageWeight.appendChild(Weight)
            from_country_code = quick_ship_id.send_addr.id and quick_ship_id.send_addr.country_id.id and quick_ship_id.send_addr.country_id.code
            to_country_code = quick_ship_id.address_id.id and quick_ship_id.address_id.country_id.id and quick_ship_id.address_id.country_id.code
            if not(from_country_code == 'US' and to_country_code == 'US' or from_country_code == 'PR' and to_country_code == 'PR'):

                ReferenceNumber = doc2.createElement("ReferenceNumber")
                Package.appendChild(ReferenceNumber)

                BarCodeIndicator = doc2.createElement("BarCodeIndicator")
                ReferenceNumber.appendChild(BarCodeIndicator)

                Code = doc2.createElement("Code")
                ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["ReferenceNumber"]["Code"])
                Code.appendChild(ptext)
                ReferenceNumber.appendChild(Code)

                Value = doc2.createElement("Value")
                ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["Shipment"]["Package"][i]["ReferenceNumber"]["Value"])
                Value.appendChild(ptext)
                ReferenceNumber.appendChild(Value)

        LabelSpecification = doc2.createElement("LabelSpecification")
        ShipmentConfirmRequest.appendChild(LabelSpecification)

        LabelPrintMethod = doc2.createElement("LabelPrintMethod")
        LabelSpecification.appendChild(LabelPrintMethod)
        Code = doc2.createElement("Code")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["LabelSpecification"]["LabelPrintMethod"]["Code"])
        Code.appendChild(ptext)
        LabelPrintMethod.appendChild(Code)

        Description = doc2.createElement("Description")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["LabelSpecification"]["LabelPrintMethod"]["Description"])
        Description.appendChild(ptext)
        LabelPrintMethod.appendChild(Description)

        LabelStockSize = doc2.createElement("LabelStockSize")
        LabelSpecification.appendChild(LabelStockSize)
        Height = doc2.createElement("Height")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["LabelSpecification"]["LabelStockSize"]["Height"])
        Height.appendChild(ptext)
        LabelStockSize.appendChild(Height)
        Width = doc2.createElement("Width")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["LabelSpecification"]["LabelStockSize"]["Width"])
        Width.appendChild(ptext)
        LabelStockSize.appendChild(Width)

        LabelImageFormat = doc2.createElement("LabelImageFormat")
        LabelSpecification.appendChild(LabelImageFormat)

        Code = doc2.createElement("Code")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["LabelSpecification"]["LabelImageFormat"]["Code"])
        Code.appendChild(ptext)
        LabelImageFormat.appendChild(Code)

        Description = doc2.createElement("Description")
        ptext = doc1.createTextNode(data_for_confirm_request["ShipmentConfirmRequest"]["LabelSpecification"]["LabelImageFormat"]["Description"])
        Description.appendChild(ptext)
        LabelImageFormat.appendChild(Description)
        ret = []
        serv = ''
        acce_port = ''
        serv_path = ''
        if quick_ship_id.logis_company.id:
            if quick_ship_id.logis_company.test_mode:
                acce_web = quick_ship_id.logis_company.ship_req_test_web or ''
                acce_port = quick_ship_id.logis_company.ship_req_test_port
            else:
                acce_web = quick_ship_id.logis_company.ship_req_web or ''
                acce_port = quick_ship_id.logis_company.ship_req_port
            if acce_web:
                parse_url = urlparse(acce_web)
                serv = parse_url.netloc
                serv_path = parse_url.path
            else:
                raise osv.except_osv(_('Unable to find Shipping URL!'),_("Please configure the shipping company with websites.") )
        else:
            raise osv.except_osv(_('No Company Selected!'),_("Please select a logistic company.") )
        request_xml = doc1.toprettyxml() + doc2.toprettyxml()
        conn = httplib.HTTPSConnection(serv,acce_port)
        res = conn.request("POST",serv_path,request_xml)
        res = conn.getresponse()
        result = res.read()
        response_dic = xml2dic.main(result)
        response = ''
        err_flag = False
        for res_elm in  response_dic['ShipmentConfirmResponse'][0]['Response']:
            if res_elm.get('ResponseStatusCode'):
                response = '\nResponse Status Code: ' + str(res_elm['ResponseStatusCode'])
            if res_elm.get('ResponseStatusDescription'):
                response += '\nResponse Description: ' + str(res_elm['ResponseStatusDescription'])
            if res_elm.get('ResponseStatusCode', False) and str(res_elm.get('ResponseStatusCode')) != 1:
                if res_elm.get('Error'):
                    err_flag = True
                    for err_elm in res_elm.get('Error'):
                        if err_elm.get('ErrorCode', False):
                            response += '\nErrorCode: ' + str(err_elm['ErrorCode'])
                        if err_elm.get('ErrorDescription', False):
                            response += '\nErrorDescription: ' + str(err_elm['ErrorDescription'])
                    self.write(cr, uid, ids, {'response': response})
        ship_digest = ""
        if len(response_dic['ShipmentConfirmResponse']) > 4 and response_dic['ShipmentConfirmResponse'][4].has_key('ShipmentDigest'):
            ship_digest += str(response_dic['ShipmentConfirmResponse'][4]['ShipmentDigest'])
        ship_move_ids = []
        value_dic = {
           'package_weight': quick_ship_id.weight,
           'state': 'in_process',
           'partner_id': quick_ship_id.recipient.id,
           'ups_service_id': quick_ship_id.ups_service_id.id,
#            'package_weight': quick_ship_id.weight,
           'ship_to': quick_ship_id.address_id.id,
           'ship_from': quick_ship_id.send_addr.id,
           'sale_id': quick_ship_id.saleorder_id.id and quick_ship_id.saleorder_id.id,
           'ship_cost': quick_ship_id.shipcharge
           }
        ship_move_id = self.pool.get('shipping.move').create(cr, uid, value_dic)
        if err_flag:
            ret = False
        else:
            ret = {'response': response, 'ship_digest': ship_digest, 'ship_move_id': ship_move_id}
        return ret

    def process_ship_accept(self, cr, uid, ids, ret_res, context=None):
        quick_ship_id = self.browse(cr, uid, ids[0], context=context)
        ship_digest=ret_res.get('ship_digest')
        data_for_Access_Request = {
            'AccessLicenseNumber': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.accesslicensenumber or '',
            'UserId': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.userid or '',
            'Password': quick_ship_id.ups_shipper_id.id and quick_ship_id.ups_shipper_id.password or ''
            }
        data_for_Ship_Accept = {
            'ShipmentAcceptRequest': {
                'Request': {
                    'RequestAction': 'ShipAccept',
                    'TransactionReference': {'CustomerContext': ''}
                    },
                'ShipmentDigest': ship_digest
                }
            }
        doc1 = Document()
        AccessRequest = doc1.createElement("AccessRequest")
        AccessRequest.setAttribute("xml:lang", "en-US")
        doc1.appendChild(AccessRequest)

        AccessLicenseNumber = doc1.createElement("AccessLicenseNumber")
        ptext = doc1.createTextNode(data_for_Access_Request["AccessLicenseNumber"])
        AccessLicenseNumber.appendChild(ptext)
        AccessRequest.appendChild(AccessLicenseNumber)

        UserId = doc1.createElement("UserId")
        ptext = doc1.createTextNode(data_for_Access_Request["UserId"])
        UserId.appendChild(ptext)
        AccessRequest.appendChild(UserId)

        Password = doc1.createElement("Password")
        ptext = doc1.createTextNode(data_for_Access_Request["Password"])
        Password.appendChild(ptext)
        AccessRequest.appendChild(Password)

        Request_string1 = doc1.toprettyxml()
        doc2 = Document()
        ShipmentAcceptRequest = doc2.createElement("ShipmentAcceptRequest")
        ShipmentAcceptRequest.setAttribute("xml:lang", "en-US")
        doc2.appendChild(ShipmentAcceptRequest)
        Request = doc2.createElement("Request")
        ShipmentAcceptRequest.appendChild(Request)

        RequestAction = doc2.createElement("RequestAction")
        ptext = doc1.createTextNode(data_for_Ship_Accept['ShipmentAcceptRequest']["Request"]['RequestAction'])
        RequestAction.appendChild(ptext)
        Request.appendChild(RequestAction)

        TransactionReference = doc2.createElement("TransactionReference")
        Request.appendChild(TransactionReference)

        CustomerContext = doc2.createElement("CustomerContext")
        ptext = doc1.createTextNode(data_for_Ship_Accept['ShipmentAcceptRequest']["Request"]['TransactionReference']['CustomerContext'])
        CustomerContext.appendChild(ptext)
        TransactionReference.appendChild(CustomerContext)

        ShipmentDigest = doc2.createElement("ShipmentDigest")
        ptext = doc1.createTextNode(data_for_Ship_Accept['ShipmentAcceptRequest']["ShipmentDigest"])
        ShipmentDigest.appendChild(ptext)
        ShipmentAcceptRequest.appendChild(ShipmentDigest)

        Request_string2 = doc2.toprettyxml()
        serv = ''
        acce_port = ''
        serv_path = ''
        if quick_ship_id.logis_company.id:
            if quick_ship_id.logis_company.test_mode:
                acce_web = quick_ship_id.logis_company.ship_accpt_test_web or ''
                acce_port = quick_ship_id.logis_company.ship_accpt_test_port
            else:
                acce_web = quick_ship_id.logis_company.ship_accpt_web or ''
                acce_port = quick_ship_id.logis_company.ship_accpt_port
            if acce_web:
                parse_url = urlparse(acce_web)
                serv = parse_url.netloc
                serv_path = parse_url.path
            else:
                raise osv.except_osv(_('Unable to find Shipping URL!'), _("Please configure the shipping company with websites.") )
        else:
            raise osv.except_osv(_('No Company Selected!'), _("Please select a logistic company.") )

        Request_string = Request_string1 + Request_string2
        conn = httplib.HTTPSConnection(serv, acce_port)
        res = conn.request("POST", serv_path, Request_string)
        res = conn.getresponse()
        result = res.read()
        response_dic = xml2dic.main(result)
        NegotiatedRates = ''
        ShipmentIdentificationNumber = ''
        TrackingNumber = ''
        if len(response_dic['ShipmentAcceptResponse']) > 1 and 'ShipmentResults' in response_dic['ShipmentAcceptResponse'][1]:
            if len(response_dic['ShipmentAcceptResponse'][1]['ShipmentResults']) > 1 and \
               'NegotiatedRates' in response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][1]:
                
                if response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][1]['NegotiatedRates'] and \
                   'NetSummaryCharges' in response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][1]['NegotiatedRates'][0]:
                    
                    if response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][1]['NegotiatedRates'][0]['NetSummaryCharges'] and \
                       'GrandTotal' in response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][1]['NegotiatedRates'][0]['NetSummaryCharges'][0]:
                        
                        NegotiatedRates = response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][1]['NegotiatedRates'][0]['NetSummaryCharges'][0]\
                                                     ['GrandTotal'][1]['MonetaryValue']
                                                     
            if response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'] and \
               'ShipmentIdentificationNumber' in response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][3]:
                
                ShipmentIdentificationNumber = response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][3]['ShipmentIdentificationNumber']
            label_image = None
            if len(response_dic['ShipmentAcceptResponse'][1]['ShipmentResults']) > 4  and \
               'PackageResults' in response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][4]:
                if response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][4]['PackageResults']:
                    TrackingNumber=response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][4]['PackageResults'][0]['TrackingNumber']
                if len(response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][4]['PackageResults']) > 2 and \
                   'LabelImage' in response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][4]['PackageResults'][2]:
                    
                    label_image =response_dic['ShipmentAcceptResponse'][1]['ShipmentResults'][4]['PackageResults'][2]['LabelImage'][1]['GraphicImage']
            if label_image:
                im_in_raw = base64.decodestring(label_image)
                path = tempfile.mktemp()
                temp = file(path, 'wb')
                temp.write(im_in_raw)
                temp.close()
                new_im = Image.open(path)
                new_im = new_im.rotate(270)
                new_im.save(path, 'JPEG')
                label_from_file = open(path, 'rb')
                label_image = base64.encodestring(label_from_file.read())
                label_from_file.close()
            self.write(cr, uid, ids, {'shipcharge': NegotiatedRates or '0', 'logo': label_image})
            if ret_res.get('ship_move_id'):
                self.write(cr,uid,ids,{'shipcharge': NegotiatedRates or '0', 'ship_log_id': ret_res.get('ship_move_id')})
                tracking_url = ''
                if TrackingNumber:
                    tracking_url = quick_ship_id.logis_company.ship_tracking_url
                    if tracking_url:
                        try:
                            tracking_url = tracking_url%TrackingNumber
                        except Exception, e:
                            tracking_url = "Invalid tracking url on shipping company"
                ship_move_id = self.pool.get('shipping.move').write(cr, uid, [ret_res.get('ship_move_id')], {
                    'logo': label_image,
                    'shipment_identific_no': ShipmentIdentificationNumber,
                    'tracking_no': TrackingNumber,
                    'tracking_url': tracking_url
                    })
        return ship_move_id

    def get_rate(self, cr, uid, ids, context=None):
        res = self.process_ship(cr, uid, ids, context=context)
        if res:
            res = self.process_ship_accept(cr, uid, ids, res, context=context)
            self.write(cr, uid, ids, {'response': ''})
        return True
    
    

    def print_label(self, cr, uid, ids, context=None):
        if not ids: return []
        ship_log_id = self.browse(cr, uid, ids, context=context)[0].ship_log_id.id
        if not ship_log_id:
            raise osv.except_osv(_('Error!'),_("Sale order is not processed."))
        return {
            'type': 'ir.actions.report.xml',
            'report_name':'ship.log.label.print',
            'datas': {
                    'model':'shipping.move',
                    'id': ship_log_id,
                    'ids': [ship_log_id],
                    'report_type': 'pdf'
                },
            'nodestroy': True
            }
        return True

quick_ship()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
