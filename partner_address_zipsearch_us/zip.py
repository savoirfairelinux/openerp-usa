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

from openerp.osv import fields,osv

class zip(osv.osv):
    '''
        New zip object to save location details 
    '''
    _name = "address.zip"
    _rec_name = "zipcode"
    _columns = {
        'zipcode': fields.char('ZIP', size=10, required=True, select=1),
        'state_id': fields.many2one('res.country.state', 'State', required=True),
        'city': fields.char('City', size=64, required=True, select=1),
        'longitude': fields.char('Longitude', size=64,),
        'latitude': fields.char('Latitude', size=64,)
        }

zip()

'''
    configuration related to zip
'''
class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'lzipmatch': fields.boolean('Use Zip-City Matching',
            help="Check this box if you want to enter zip codes with addresses and it search/populate city/state/longitude/latitude"),
        }

res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
