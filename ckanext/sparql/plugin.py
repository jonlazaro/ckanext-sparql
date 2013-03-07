# -*- coding: utf8 -*- 

from ckan.plugins import SingletonPlugin, IGenshiStreamFilter, implements, IConfigurer, IRoutes
from logging import getLogger
from pylons import request
from genshi.input import HTML
from genshi.filters.transform import Transformer
import ckan.model as model
import os

from sparql_model.model import SparqlEnpoint

log = getLogger(__name__)

class SPARQLExtension(SingletonPlugin):    
    implements(IConfigurer, inherit=True)
    implements(IGenshiStreamFilter, inherit=True)
    implements(IRoutes, inherit=True)
    
    def update_config(self, config):
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        our_public_dir = os.path.join(rootdir, 'ckanext', 
                'sparql', 'theme', 'public')
                                      
        template_dir = os.path.join(rootdir, 'ckanext',
                'sparql', 'theme', 'templates')
                
        # set resource and template overrides
        config['extra_public_paths'] = ','.join([our_public_dir,
                config.get('extra_public_paths', '')])
                
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])

    def filter(self, stream):
        routes = request.environ.get('pylons.routes_dict')                
        if routes.get('controller') in ('admin', 'ckanext.sparql.controller:SparqlAdminController'):
            isactive = 'active' if routes.get('controller') == 'ckanext.sparql.controller:SparqlAdminController' else ''
            stream = stream | Transformer('//ul[@class="nav nav-pills"]').append(HTML(
                    '''<li class="''' + isactive + '''">
                        <a class href="/ckan-admin/sparql-config">
                            SPARQL Endpoint Configuration
                        </a>
                    </li>'''
                ))

        if model.Session.query(SparqlEnpoint).filter_by(isglobal=True, isenabled=True).first():
            stream = stream | Transformer('//div[@id="mainmenu"]').append(HTML(
                    '''<a class="" href="/sparql">SPARQL Endpoint</a>'''
                ))

        return stream

    def before_map(self, map):
        map.connect('/ckan-admin/sparql-config',
            controller='ckanext.sparql.controller:SparqlAdminController',
            action='sparql_config')

        map.connect('/sparql',
            controller='ckanext.sparql.controller:SparqlGuiController',
            action='sparql_endpoint')

        return map