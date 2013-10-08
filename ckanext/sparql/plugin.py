# -*- coding: utf8 -*-

from ckan.plugins import SingletonPlugin, IGenshiStreamFilter, implements, IConfigurer, IRoutes
from logging import getLogger
from pylons import request, tmpl_context as c
from genshi.input import HTML
from genshi.filters.transform import Transformer
import ckan.model as model
import os
from ckan.lib.helpers import check_access

from sparql_model.model import SparqlEndpoint
from ckan.model.package import Package

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

        if model.Session.query(SparqlEndpoint).filter_by(isglobal=True, isenabled=True).first():
            stream = stream | Transformer('//div[@id="mainmenu"]').append(HTML(
                    '''<a class="" href="/sparql">SPARQL Endpoint</a>'''
                ))

        try:
            packageid = c.pkg.id
        except:
            packageid = None

        if packageid:
            if routes.get('controller') in ('package', 'related', 'ckanext.sparql.controller:SparqlPackageController'):
                sparqlendpoint = model.Session.query(SparqlEndpoint).filter(SparqlEndpoint.packages.any(Package.name == routes.get('id'))).first()
                htmlstr = ''
                isactive = 'active' if routes.get('controller') == 'ckanext.sparql.controller:SparqlPackageController' else ''
                if (sparqlendpoint and sparqlendpoint.isenabled) or check_access('package_update', {'id':packageid}):
                    htmlstr += '''<li class="dropdown ''' + isactive + '''">
                                  <a class="dropdown-toggle" data-toggle="dropdown" href="#"><img src="/icons/rdf_flyer.24" height="16px" width="16px" alt="None" class="inline-icon ">SPARQL Endpoint<b class="caret"></b></a>
                                  <div class="dropdown-appears">
                                    <ul class="dropdown-menu">'''

                    if sparqlendpoint.isenabled:
                        htmlstr += '''<li>
                                        <a href="/dataset/%s/sparql"><img src="/images/icons/package.png" height="16px" width="16px" alt="None" class="inline-icon "> Query SPARQL Endpoint</a>
                                      </li>''' % routes.get('id')

                    if check_access('package_update', {'id':packageid}):
                        htmlstr += '''<li>
                                <a href="/dataset/%(id)s/edit/sparql"><img src="/images/icons/package_edit.png" height="16px" width="16px" alt="None" class="inline-icon "> Configure SPARQL Endpoint</a>
                              </li>''' % {'id': routes.get('id')}
                    htmlstr += '''</ul>
                              </div>
                            </li>'''
                stream = stream | Transformer('//ul[@class="nav nav-pills"]').append(HTML(htmlstr))

        return stream

    def before_map(self, map):
        map.connect('/ckan-admin/sparql-config',
            controller='ckanext.sparql.controller:SparqlAdminController',
            action='sparql_config')

        map.connect('/sparql',
            controller='ckanext.sparql.controller:SparqlGuiController',
            action='sparql_endpoint')

        map.connect('/dataset/{id}/edit/sparql',
            controller='ckanext.sparql.controller:SparqlPackageController',
            action='sparql_config')

        map.connect('/dataset/{id}/uploadrdf',
            controller='ckanext.sparql.controller:SparqlPackageController',
            action='sparql_config')

        map.connect('/dataset/{id}/sparql',
            controller='ckanext.sparql.controller:SparqlPackageController',
            action='sparql_endpoint')

        return map
