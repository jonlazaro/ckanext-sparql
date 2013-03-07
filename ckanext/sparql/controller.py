# -*- coding: utf8 -*- 

from ckan.lib.base import render, c, request, _
from logging import getLogger
from ckan.lib.base import BaseController, abort
from ckan.logic import get_action, NotFound
from sparql_model.model import SparqlEnpoint

import ckan.authz
import ckan.model as model
import ConfigParser
import os

log = getLogger(__name__)


class SparqlGuiController(BaseController):
    # Check if the user is admin (based on CKAN's AdminController)
    def __before__(self, action, **params):
        super(SparqlGuiController, self).__before__(action, **params)
        if not model.Session.query(SparqlEnpoint).filter_by(isglobal=True, isenabled=True).first():
            abort(404)

    def sparql_endpoint(self):
        c.resultformats = {'html': 'HTML'}
        return render('sparql/sparq_gui.html')


class SparqlAdminController(BaseController):
    # Check if the user is admin (based on CKAN's AdminController)
    def __before__(self, action, **params):
        super(SparqlAdminController, self).__before__(action, **params)
        if not ckan.authz.Authorizer().is_sysadmin(unicode(c.user)):
            abort(401, _('Need to be system administrator to administer'))
        c.revision_change_state_allowed = (
            c.user and self.authorizer.is_authorized(c.user,
                                                     model.Action.CHANGE_STATE,
                                                     model.Revision))

    def sparql_config(self):
        log.info('Entering to main SPARQL configurer')

        c.storeconfigform = {}

        globalendpointquery = model.Session.query(SparqlEnpoint).filter_by(isglobal=True)
        globalendpoint = globalendpointquery.first()

        conf_file = ConfigParser.ConfigParser()
        conf_file.read(os.environ['CKAN_CONFIG'])
        c.storeconfigform['endpoint_name'] = globalendpoint.name if globalendpoint else conf_file.get('app:main', 'ckan.site_title')
        c.storeconfigform['endpoint_sparqlurl'] = globalendpoint.sparqlurl if globalendpoint else ''
        c.storeconfigform['endpoint_sparulurl'] = globalendpoint.sparulurl if globalendpoint else ''
        c.storeconfigform['endpoint_graph'] = globalendpoint.graph if globalendpoint else ''
        c.storeconfigform['endpoint_endpointtype'] = globalendpoint.storetype if globalendpoint else 'virtuoso'
        c.storeconfigform['endpoint_user'] = globalendpoint.username if globalendpoint else None
        c.storeconfigform['endpoint_passwd'] = globalendpoint.passwd if globalendpoint else None
        c.storeconfigform['endpoint_dataallowed'] = globalendpoint.isdataallowed if globalendpoint else True
        c.storeconfigform['endpoint_enabled'] = globalendpoint.isenabled if globalendpoint else None
        c.storeconfigform['endpoint_authrequired'] = globalendpoint.isauthrequired if globalendpoint else False

        c.endpointtypes = {'virtuoso': 'OpenLink Virtuoso', 'sparql11': 'SPARQL 1.1 Endpoint'}
        
        if 'save' in request.params:
            # It's POST call after form
            errors = False
            for field, value in request.params.items():
                if not value and field not in ['user', 'passwd']:
                    c.form_error = field
                    c.error_message = "Required fields unfilled"
                    errors = True
                    break
                c.storeconfigform['endpoint_' + field] = value
            if not errors:
                datadict = {
                    'name': c.storeconfigform['endpoint_name'],
                    'sparqlurl': c.storeconfigform['endpoint_sparqlurl'],
                    'sparulurl': c.storeconfigform['endpoint_sparulurl'],
                    'graph': c.storeconfigform['endpoint_graph'],
                    'storetype': c.storeconfigform['endpoint_endpointtype'],
                    'username': c.storeconfigform['endpoint_user'] if c.storeconfigform['endpoint_authrequired'] else None,
                    'passwd': c.storeconfigform['endpoint_passwd'] if c.storeconfigform['endpoint_authrequired'] else None,
                    'isauthrequired': True if c.storeconfigform['endpoint_authrequired'] in ['on', True] else False,
                    'isglobal': True,
                    'isdataallowed': True if c.storeconfigform['endpoint_dataallowed'] in ['on', True] else False,
                    'isenabled': c.storeconfigform['endpoint_enabled'] if globalendpoint else True
                }                

                if globalendpoint:
                    if dict((name, getattr(globalendpoint, name)) for name in dir(globalendpoint) if name in datadict.keys()) != datadict:
                        log.info('Updating object in database...')
                        globalendpointquery.update(datadict)
                    else:
                        log.info('No changes')
                else:
                    log.info('Creating new object in database...')
                    endpointdb = SparqlEnpoint(datadict)
                    model.Session.add(endpointdb)

                model.Session.commit()

        elif 'enable' in request.params:
            if globalendpoint:
                globalendpointquery.update({'isenabled': True})
                c.storeconfigform['endpoint_enabled'] = True
                log.info('Enabling rdf store...')
                model.Session.commit()

        elif 'disable' in request.params:
            if globalendpoint:
                globalendpointquery.update({'isenabled': False})
                c.storeconfigform['endpoint_enabled'] = False
                log.info('Disabling rdf store...')
                model.Session.commit()

        return render('admin/admin_sparql.html')