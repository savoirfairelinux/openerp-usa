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

class shipping_label_type(osv.osv):
    _name = 'shipping.label.type'
    _columns = {
        'name': fields.char('Label Type', size=32, required=True),
        'code': fields.selection([('EPL','EPL'),('ZPL','ZPL'),('GIF','GIF')], required=True),
        'http_user_agent' :fields.char('HTTP User Agent', size=64),
        'width': fields.float('Width'),
        'height': fields.float('Height'),
    }

shipping_label_type()