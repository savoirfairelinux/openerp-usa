# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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
import pooler
import sys
import traceback
from osv import osv, fields
from tools.safe_eval import safe_eval
from tools import DEFAULT_SERVER_DATETIME_FORMAT


class external_report_lines(osv.osv):
    _name = 'external.report.line'
    _description = 'External Report Lines'
    _rec_name = 'res_id'
    _order = 'date desc'

    _columns = {
        'res_model': fields.char('Resource Object', size=64,
                                 required=True, readonly=True),
        'res_id': fields.integer('Resource Id', readonly=True),
        'action': fields.char('Action', size=32, required=True, readonly=True),
        'date': fields.datetime('Date', required=True, readonly=True),
        'external_id': fields.char('External ID', size=64, readonly=True),
        'error_message': fields.text('Error Message', readonly=True),
        'traceback': fields.text('Traceback', readonly=True),
        'exception_type': fields.char('Exception Type', size=128, readonly=True),
        'data_record': fields.serialized('External Data', readonly=True),
        'origin_defaults': fields.serialized('Defaults', readonly=True),
        'origin_context': fields.serialized('Context', readonly=True),
        'referential_id': fields.many2one(
            'external.referential', 'External Referential',
            required=True, readonly=True)
    }

    _defaults = {
        "date": lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    }

    def _prepare_log_vals(self, cr, uid, model, action, res_id,
        external_id, referential_id, data_record, context=None):
        return {
            'res_model': model,
            'action': action,
            'res_id': res_id,
            'external_id': external_id,
            'referential_id': referential_id,
            'data_record': data_record,
        }

    def _prepare_log_info(self, cr, uid, origin_defaults, origin_context, context=None):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return {
            'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'origin_defaults': origin_defaults,
            'origin_context': origin_context,
            'exception_type': exc_type,
            'error_message': exc_value,
            'traceback': ''.join(traceback.format_exception(
                exc_type, exc_value, exc_traceback)),
        }

    def log_failed(self, cr, uid, model, action, referential_id,
                  res_id=None, external_id=None,
                  data_record=None, defaults=None, context=None):
        defaults = defaults or {}
        context = context or {}
        existing_line_id = context.get('retry_report_line_id', False)

        # if the log was a fail, we raise to not let the import continue
        # This ensure a backward compatibility, synchro will continue to
        # work exactly the same way if use_external_log is not in context
        if not(existing_line_id or context.get('use_external_log', False)):
            raise

        log_cr = pooler.get_db(cr.dbname).cursor()

        try:
            origin_defaults = defaults.copy()
            origin_context = context.copy()
            # connection object can not be kept in text indeed
            # FIXME : see if we have some problem with other objects
            # and maybe remove from the conect all objects
            # which are not string, boolean, list, dict, integer, float or ?
            if origin_context.get('conn_obj', False):
                del origin_context['conn_obj']
            info = self._prepare_log_info(
                log_cr, uid, origin_defaults, origin_context, context=context)
            if existing_line_id:
                self.write(
                    log_cr, uid,
                    existing_line_id,
                    info,
                    context=context)
            else:
                vals = self._prepare_log_vals(
                    log_cr, uid, model, action, res_id, external_id,
                    referential_id, data_record, context=context)
                vals.update(info)
                existing_line_id = self.create(
                    log_cr, uid, vals,
                    context=context)
        except:
            log_cr.rollback()
            raise
        else:
            log_cr.commit()
        finally:
            log_cr.close()
        return existing_line_id

    def log_success(self, cr, uid, model, action, referential_id,
            res_id=None, external_id=None, context=None):
        if res_id is None and external_id is None:
            raise ValueError('Missing ext_id or external_id')
        domain = [
            ('res_model', '=', model),
            ('action', '=', action),
            ('referential_id', '=', referential_id),
        ]
        if res_id is not None:
            domain += ('res_id', '=', res_id),
        if external_id is not None:
            domain += ('external_id', '=', external_id),
        log_cr = pooler.get_db(cr.dbname).cursor()
        try:
            log_ids = self.search(
                log_cr, uid, domain, context=context)
            self.unlink(log_cr, uid, log_ids, context=context)
        except:
            log_cr.rollback()
            raise
        else:
            log_cr.commit()
        finally:
            log_cr.close()
        return True

    def retry(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        for log in self.browse(cr, uid, ids, context=context):
            mapping = self.pool.get(log.res_model).\
            report_action_mapping(cr, uid, context=context)

            method = mapping.get(log.action, False)
            if not method:
                raise Exception("No python method defined for action %s" %
                                (log.action,))

            kwargs = {}
            for field, value in method['fields'].items():
                kwargs[field] = safe_eval(value, {'log': log, 'self': self})

            if not kwargs.get('context', False):
                kwargs['context'] = {}

            # keep the id of the line to update it with the result
            kwargs['context']['retry_report_line_id'] = log.id
            # force export of the resource
            kwargs['context']['force_export'] = True
            kwargs['context']['force'] = True

            method['method'](cr, uid, **kwargs)
        return True

external_report_lines()
