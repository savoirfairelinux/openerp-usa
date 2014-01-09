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
from openerp import netsvc
from openerp.tools.translate import _

class shipping_rate_card(osv.osv):
    _name = 'shipping.rate.card'
    _description = "Ground Shipping Calculation Table"
    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'from_date': fields.datetime('From Date'),
        'to_date': fields.datetime('To Date'),
        'rate_ids': fields.one2many('shipping.rate', 'card_id', 'Shipping Rates', required=True),
    }

shipping_rate_card()

class shipping_rate_config(osv.osv):
    _name = 'shipping.rate.config'
    _description = "Configuration for shipping rate"
    _rec_name = 'shipmethodname'

    _columns = {
        'real_id': fields.integer('ID', readonly=True, ),
        'shipmethodname': fields.char('Name', size=128, help='Shipping method name. Displayed in the wizard.'),
        'active': fields.boolean('Active', help='Indicates whether a shipping method is active'),
        'use': fields.boolean('Select'),
        'calc_method': fields.selection([
            ('country_weight', 'Country & Weight'),
            ('state_zone_weight', 'State-Zone-Weight'),
            ('manual', 'Manually Calculate')
            ], 'Shipping Calculation Method', help='Shipping method name. Displayed in the wizard.'),
        'shipping_wizard': fields.integer('Shipping Wizard'),
        'zone_map_ids': fields.one2many('zone.map', 'rate_config_id', 'Zone Map'),
        'account_id': fields.many2one('account.account', 'Account', help='This account represents the g/l account for booking shipping income.'),
        'shipment_tax_ids': fields.many2many('account.tax', 'shipment_tax_rel', 'shipment_id', 'tax_id', 'Taxes', domain=[('parent_id', '=', False)]),
        'rate_card_id': fields.many2one('shipping.rate.card', 'Shipping Rate Card')
    }
    
    _defaults = {
        'calc_method': 'country_weight'
    }

shipping_rate_config()

class zone_map(osv.osv):
    _name = 'zone.map'
    _description = "Zone Mapping Table"
    _rec_name = 'zone'
    
    _columns = {
        'zone': fields.integer('Zone'),
        'state_id': fields.many2one('res.country.state', 'State / Zone'),
        'rate_config_id': fields.many2one('shipping.rate.config', 'Shipping Rate Configuration')
    }

zone_map()

class shipping_rate(osv.osv):
    _name = 'shipping.rate'
    _description = "Shipping Calculation Table"
    
    _columns = {
        'name': fields.char('Name', size=128),
        'from_weight': fields.integer('From Weight', required=True),
        'to_weight': fields.integer('To Weight'),
        'charge': fields.float('Shipping Charge'),
        'over_cost': fields.float('Shipping Charge per pound over'),
        'country_id': fields.many2one('res.country', 'Country'),
        'zone': fields.integer('Zone', required=True),
        'card_id': fields.many2one('shipping.rate.card', 'Shipping Table')
    }

    def find_cost(self, cr, uid, config_id, address, model_obj, context=None):
        """
        Function to calculate shipping cost
        """
        cost = 0
        table_pool = self.pool.get('shipping.rate')
        config_pool = self.pool.get('shipping.rate.config')
        logger = netsvc.Logger()
        config_obj = config_pool.browse(cr, uid, config_id, context=context)
        rate_card_id = config_obj.rate_card_id.id        
        if config_obj.calc_method == 'country_weight':
            country_id = address.country_id.id
            weight_net = model_obj.total_weight_net
            table_ids = table_pool.search(cr, uid, [('card_id', '=', rate_card_id),('country_id', '=', country_id),
                                                    ('from_weight', '<=', weight_net), ('to_weight', '>', weight_net)],context=context)
            if table_ids:
                table_obj = table_pool.browse(cr, uid, table_ids[0], context=context)
                if table_obj.charge == 0.0 and table_obj.over_cost:
                    cost = model_obj.total_weight_net * table_obj.over_cost
                else:
                    cost = table_obj.charge

            else:
                search_list = [('card_id', '=', rate_card_id), ('country_id', '=', country_id), ('over_cost', '>', 0)]
                table_ids = table_pool.search(cr, uid, search_list, context=context)
                if table_ids:
                    table_objs = table_pool.browse(cr, uid, table_ids, context=context)
                    table_obj = table_objs[0]
                    for table in table_objs:
                        if table_obj.from_weight < table.from_weight:
                            table_obj = table
                    weight = model_obj.total_weight_net
                    if table_obj.charge > 0:
                        cost = table_obj.charge
                        weight -= table_obj.from_weight
                        if weight>0:
                            cost += weight * table_obj.over_cost
                    else:
                        cost = weight * table_obj.over_cost
                else:
                    logger.notifyChannel(_("Calculate Shipping"), netsvc.LOG_WARNING, _("Unable to find rate table with Shipping Table = %s and \
                                            Country = %s and Over Cost > 0."%(config_obj.rate_card_id.name, address.country_id.name)))

        elif config_obj.calc_method == 'state_zone_weight':
            zone_pool = self.pool.get('zone.map')
            state_id = address.state_id.id
            zone_ids = zone_pool.search(cr, uid, [('rate_config_id', '=', config_obj.id),('state_id', '=', state_id)], context=context)
            if zone_ids:
                zone = zone_pool.read(cr, uid, zone_ids, ['zone'], context=context)[0]['zone']
                table_ids = table_pool.search(cr, uid, [('card_id', '=', rate_card_id), ('zone', '=', zone)], context=context)
                if table_ids:
                    table_obj = table_pool.browse(cr, uid, table_ids, context=context)[0]
                    weight = model_obj.total_weight_net
                    if table_obj.charge > 0:
                        cost = table_obj.charge
                        weight -= table_obj.to_weight
                        if weight > 0:
                            cost += weight*table_obj.over_cost
                    else:
                        cost = weight*table_obj.over_cost
                else:
                    logger.notifyChannel(_("Calculate Shipping"), netsvc.LOG_WARNING, _("Unable to find rate table with Shipping Table = %s and \
                                            Zone = %s."%(config_obj.shipmethodname, zone)))
            else:
                logger.notifyChannel(_("Calculate Shipping"), netsvc.LOG_WARNING, _("Unable to find Zone Mapping Table with Shipping Rate \
                                        Configuration = %s and State = %s."%(config_obj.shipmethodname, address.state_id.name)))
        elif config_obj.calc_method == 'manual':
            cost = 0.0
        return cost

shipping_rate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: