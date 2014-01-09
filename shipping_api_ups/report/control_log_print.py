# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
import base64

from report import report_sxw
from openerp.osv import osv,fields

class report_sxw_new(report_sxw.report_sxw):
    def __init__(self, name, table, rml=False, parser=report_sxw.rml_parse, header='external', store=False):
        super(report_sxw_new, self).__init__(name, table, rml, parser, header, store)

    def create_single_pdf(self, cr, uid, ids, data, report_xml, context=None):
        package = self.pool.get('stock.packages').browse(cr, uid, ids[0], context=context)
        report_content = ''
        control_receipt = package.control_log_receipt
        if control_receipt:
            control_receipt = base64.decodestring(control_receipt)
            from xhtml2pdf.default import DEFAULT_CSS
            from xhtml2pdf.document import pisaDocument
            import sys
            import tempfile
            CreatePDF = pisaDocument
            path = tempfile.mktemp() + '.html'
            temp = file(path, 'wb')
            temp.write(control_receipt)
            temp.close()
            fsrc = open(path, 'rb')
            dest_file = tempfile.mktemp() + '.pdf'
            fdest = open(dest_file, 'wb')
            pdf = pisaDocument(fsrc, fdest, debug=0, path = path, errout = sys.stdout,
                               tempdir = None, format = 'pdf', link_callback = None,
                               default_css = None, xhtml = False, encoding = None, xml_output = None)
            fdest.close()
            out_file = open(dest_file, 'rb')
            report_content = out_file.read()
            out_file.close()
            
        report_xml.report_type = "pdf"        
        return (report_content, report_xml.report_type)

class report_print_control_log(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_label, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
        })  

report_sxw_new(
    'report.control.log.receipt.print',
    'stock.packages',
    '',
    parser=report_print_control_log, header=False
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: