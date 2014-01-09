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
import xmlrpclib

server = 'localhost'
port = '8069'
secure = False
username = 'admin'
password = 'admin'
dbname = 'sale_promotions'

url = 'http' + (secure and 's' or '') + '://' + server + ':' + port
common = xmlrpclib.ServerProxy(url + '/xmlrpc/common')
uid = common.login(dbname, username, password)
object = xmlrpclib.ServerProxy(url + '/xmlrpc/object')
#object.execute(dbname, uid, password,'promos.rules', 'evaluate', 1, 3) #TODO: evaluate def need object, not ID values
object.execute(dbname, uid, password, 'promos.rules', 'apply_promotions', 3)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: