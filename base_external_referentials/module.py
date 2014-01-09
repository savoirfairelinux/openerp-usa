# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
#    trouver un nom    for OpenERP                                              #
#    Copyright (C) 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>   #
#                                                                               #
#    This program is free software: you can redistribute it and/or modify       #
#    it under the terms of the GNU Affero General Public License as             #
#    published by the Free Software Foundation, either version 3 of the         #
#    License, or (at your option) any later version.                            #
#                                                                               #
#    This program is distributed in the hope that it will be useful,            #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
#    GNU Affero General Public License for more details.                        #
#                                                                               #
#    You should have received a copy of the GNU Affero General Public License   #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                               #
#################################################################################

import addons
import os
from tools import osutil


#The way I implement autoload feature is not stable https://code.launchpad.net/~sebastien.beau/openobject-server/autoload/+merge/84512
#Moreover hidding dependency look to be a bad idea
#I will remove this code soon after refactoring the module that use it
addons.load_module_graph_ori = addons.load_module_graph

def load_module_graph(cr, graph, status=None, perform_checks=True, skip_modules=None, **kwargs):
    for package in graph:
        if package.state  in ('to install', 'to upgrade'):
            mapping_dir = os.path.join(addons.get_module_path(package.name), 'autoload')
            exist = os.path.exists(mapping_dir)
            if exist:
                for mapping_module in osutil.listdir(mapping_dir):    
                    cr.execute("select id from ir_module_module where name = '%s' and state in ('installed', 'to_update');"%mapping_module)
                    res = cr.fetchall()
                    if res:
                        mapping_module_dir = os.path.join(mapping_dir, mapping_module)
                        files = osutil.listdir(mapping_module_dir, recursive=True)
                        for file in files:
                            if file[-4:] in ['.csv', '.xml']:
                                package.data['update_xml'].append('autoload/%s/%s'%(mapping_module,file))
    return addons.load_module_graph_ori(cr, graph, status, perform_checks, skip_modules, **kwargs)

addons.load_module_graph = load_module_graph


#The funciton is_installed will be not merge https://code.launchpad.net/~sebastien.beau/openobject-server/add_function_is_installed/+merge/84474
#Hidding dependency seem not to be a good idea, I extend the class here in order to use this solution before finding a good one
class module(osv.osv):
    _inherit = "ir.module.module"

    def is_installed(self, cr, uid, module_name, context=None):
        return bool(self.search(cr, 1, [['name', '=', module_name], ['state', 'in', ['installed', 'to upgrade']]], context=context))

