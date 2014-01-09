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
from datetime import datetime, timedelta
import time
import pytz

cron_descriptor = {
        'name'            : 'Currency update process',
        'active'          : True,
        'priority'        : 1,
        'interval_number' : 10,
        'interval_type'   : 'minutes',
        'nextcall'        : time.strftime("%Y-%m-%d %H:%M:%S", (datetime.today() + timedelta(minutes=10)).timetuple()),
        'numbercall'      : -1,
        'doall'           : True,
        'model'           : 'res.currency',
        'function'        : 'scheduler_tick',
        'args'            : '()',
}

class res_currency(osv.osv):
    _inherit = "res.currency"

    def _get_update_selection(self, cr, uid, context=None):
        return self.get_update_selection(cr, uid, context=context) or []

    _columns = {
        'update_method': fields.selection (_get_update_selection, 'Update method', required=True),   
        'currency_code': fields.char ('External currency code', size=128, help="External identification used by the update service to get the current currency rate"),
        'update_time': fields.selection([("%02d.%02d" %(hours, minutes), "%d.%d hs" %(hours, minutes))  for minutes in [0, 30] for hours in range(0,24)], 'Update time'),
        'last_update_on': fields.date('Last succesfull update on'),
        'update_timezone': fields.selection([(x,x) for x in pytz.common_timezones], 'Update timezone'),
        'log_buffer': fields.text('Service log'),
    }
    
    _defaults = {
        'update_method': 'manual',
        'update_time': '08.30',
        'last_update_on': '2012-01-01',
        'update_timezone': 'UTC',
    }

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not context.get('buffer',False):
            self.set_cron_task(cr, uid, context=context)
        return super(res_currency, self).write(cr, uid, ids, vals, context=context)        
        
    # Method to be subclassed by plugins
    def get_update_selection(self, cr, uid, context=None):
        return [('manual', 'Manual')]
        
    def update_rate(self, cr, uid, ids, context=None):
        return True

    # End of plugins

    def set_cron_task(self, cr, uid, context=None):
        cron_obj = self.pool.get('ir.cron')
        cron_ids = cron_obj.search(cr, uid, [('function', 'ilike', cron_descriptor['function']),
                                             ('model', 'ilike', cron_descriptor['model'])],
                                      context={'active_test': False})
        if not cron_ids :
            cron_id = cron_obj.create(cr, uid, cron_descriptor, context=context)
        else:
            cron_id = cron_ids
            cron_obj.write(cr, uid, cron_ids, cron_descriptor, context=context)
        
        return cron_id
        
    def scheduler_tick(self, cr, uid, context=None):
        possible_ids = self.search(cr, uid, [('update_method','!=','manual')], context=context)
        if not possible_ids:
            return True
            
        candidates_ids = []
        
        for c in self.browse(cr, uid, possible_ids, context=context):
            local_now = datetime.now(pytz.timezone(c.update_timezone))
            local_date = "%4d-%02d-%02d" % (local_now.year, local_now.month, local_now.day)
            local_time = "%02d.%02d" % (local_now.hour, local_now.minute)
            if c.last_update_on != local_date or local_time >= c.update_time:
                candidates_ids.append(c.id)

        if candidates_ids:
            candidates = self.browse(cr, uid, candidates_ids, context=context)
            methods = set([c.update_method for c in candidates])
            method_currencies = {}
            for m in methods: method_currencies[m] = [] #YT 2012/01/08: method_currencies = {m:[] for m in methods}
            for c in candidates:
                method_currencies[c.update_method].append(c.id)
            for mc in method_currencies.keys():
                self.update_rate(cr, uid, method_currencies[mc], context=context)
                
#         self.set_cron_task(cr, uid, context=context)
        return True

    def log_add(self, cr, uid, ids, add_lines, context=None):
        if context is None:
            context = {}
        for c in self.browse(cr, uid, ids, context=context):
            lines = (c.log_buffer or ' ').split('\n')
            ctx = context.copy()
            ctx.update({'buffer':True})
            c.write({'log_buffer': add_lines+'\n'+('\n'.join(lines[0:-2]))}, context=ctx)
            
    def rate_add(self, cr, uid, ids, rate_type_id, value, context=None):
        rcr_obj = self.pool.get('res.currency.rate')
        today = fields.date.context_today(self, cr, uid, context=context)
        for c in self.browse(cr, uid, ids, context=None):
            rate_ids = rcr_obj.search(cr, uid, [('name','=',today),('currency_id','=',c.id),('currency_rate_type_id','=',rate_type_id)], context=context)
            if not rate_ids:
                rcr_obj.create (cr, uid, {
                            'name': today,
                            'rate': value,
                            'currency_id': c.id,
                            'currency_rate_type_id': rate_type_id,
                        }, context=context)                                                                        
            else:
                rcr_obj.write (cr, uid, rate_ids, {
                            'rate': value,                    
                        })
        return True
        
