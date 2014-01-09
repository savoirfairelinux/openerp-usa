# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
# Copyright (c) 2011 NUMA Extreme Systems (www.numaes.com) for Cubic ERP - Teradata SAC. (http://cubicerp.com).
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
from tools.translate import _
import netsvc
import logging

logger = logging.getLogger(__name__)


def get_url(url):
    """Return a string of a get url query"""
    try:
        import urllib
        objfile = urllib.urlopen(url)
        rawfile = objfile.read()
        objfile.close()
        return rawfile
    except ImportError:
        raise Exception ('Error: Unable to import urllib !')
    except IOError:
        raise Exception ('Error: Web Service [%s] does not exist or it is non accesible !' % url)


def get_yahoo_rates(from_currency, to_currency):
    url='http://finance.yahoo.com/d/quotes.txt?s="%s"=X&f=sba'
    
    data = get_url(url % (from_currency+to_currency))
    if data:
        logger.info("[%s] %s", netsvc.LOG_DEBUG, "YAHOO sent a response")
    else:
        raise Exception ('Error retrieving info from YAHOO FINANCE. No data retrieved')

    values = data.split(',')
    try:
        ret = {
        'current_sale_ratio': float(values[1]),
        'current_purchase_ratio': float(values[2]),
        }
        return ret
    except Exception, e:
        logger.info("[%s] %s", netsvc.LOG_DEBUG, "YAHOO FINANCE exception for %s : %s" % (to_currency,values))
        return False

class res_currency(osv.osv):
    _inherit = "res.currency"

    # Method to be subclassed by plugins
    def get_update_selection(self, cr, uid, context=None):
        return [('yahoo', 'YAHOO Finance')] + super(res_currency, self).get_update_selection(cr, uid, context=context)
        
    def update_rate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if ids:
            yahoo_ids = [c.id for c in self.browse(cr, uid, ids, context=context) if c.update_method=='yahoo']
            if yahoo_ids:
                try:
                    base_currency_ids = self.search(cr, uid, [('base','=',True)], context=context)
                    if not base_currency_ids:
                        raise Exception('Error retrieving info for YAHOO: No base currency found!')
                    base_currency = self.browse(cr, uid, base_currency_ids[0], context=context)

                    sale_type_id = self.get_sale_type_id(cr, uid, context=context)
                    purchase_type_id = self.get_purchase_type_id(cr, uid, context=context)

                    for c in self.browse(cr, uid, ids, context=context):
                        rates = get_yahoo_rates(base_currency.name, c.name)
                        if not rates:
                            continue
                        self.rate_add(cr, uid, [c.id], sale_type_id, rates['current_sale_ratio'], context=context)
                        self.rate_add(cr, uid, [c.id], purchase_type_id, rates['current_purchase_ratio'], context=context)
                        self.rate_add(cr, uid, [c.id], False, (rates['current_purchase_ratio']+rates['current_sale_ratio'])/2.0, context=context)
                        ctx = context.copy()
                        ctx.update({'buffer':True})
                        c.write({'last_update_on': fields.date.context_today(self, cr, uid, context=context),
                                 'log_buffer':'OK'}, context=ctx)
                        logger.info("[%s] %s", netsvc.LOG_DEBUG, "YAHOO successful update on currency %s" % c.name)
                                                            
                except Exception, e:
                    logger.info("[%s] %s", netsvc.LOG_DEBUG, "YAHOO unexpected exception: %s" % unicode(e))
                    ctx = context.copy()
                    ctx.update({'buffer':True})
                    self.log_add(cr, uid, ids, _("Exception on %s: %s") % (fields.datetime.now(), unicode(e)), context=ctx)
        return super(res_currency, self).update_rate(cr, uid, ids, context=context)    

    # End of plugins

    def get_sale_type_id(self, cr, uid, context=None):
        rcrt_obj = self.pool.get('res.currency.rate.type')
        sale_ids = rcrt_obj.search(cr, uid, [('name','=','Venta')], context=context)
        if not sale_ids:
            sale_id = rcrt_obj.create(cr, uid, {'name': 'Venta'}, context=context)
        else:
            sale_id = sale_ids[0]
        return sale_id
        
    def get_purchase_type_id(self, cr, uid, context=None):
        rcrt_obj = self.pool.get('res.currency.rate.type')
        purchase_ids = rcrt_obj.search(cr, uid, [('name','=','Compra')], context=context)
        if not purchase_ids:
            purchase_id = rcrt_obj.create(cr, uid, {'name': 'Compra'}, context=context)
        else:
            purchase_id = purchase_ids[0]
            
        return purchase_id
        
