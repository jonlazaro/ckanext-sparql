# -*- coding: utf8 -*- 

from ckan.lib.base import render, c, request, _
from logging import getLogger
from ckan.lib.base import BaseController, abort
from ckan.logic import get_action, NotFound
from sparql_model.model import SparqlEndpoint
from ckan.controllers.package import PackageController
from ckan.model.package import Package
from pylons import url

import ckan.authz
import ckan.model as model
import ConfigParser
import os
#import rdflib

log = getLogger(__name__)

ENDPOINT_TYPES = {'virtuoso': 'OpenLink Virtuoso', 'sparql11': 'SPARQL 1.1 Endpoint'}

class SparqlPackageController(PackageController):
    def __before__(self, action, **params):
        super(SparqlPackageController, self).__before__(action, **params)
        self.packageendpointquery = model.Session.query(SparqlEndpoint).filter(SparqlEndpoint.packages.any(Package.name == c.environ['pylons.routes_dict']['id']))
        self.packageendpoint = self.packageendpointquery.first()
        if c.action == 'sparql_endpoint' and (not self.packageendpoint or not self.packageendpoint.isenabled):
            abort(404)

    def sparql_endpoint(self, id):
        # using default functionality
        template = self.read(id)

        #check if metadada info exists and add it otherwise
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author}
        package_info = get_action('package_show')(context, {'id': c.pkg.id})


        c.resultformats = {'html': 'HTML'}

        if 'runquery' in request.params:
            errors = False
            #g = rdflib.ConjunctiveGraph('SPARQLStore')
            #g.open("
            # Run query
            
            if errors:
                c.error_message = 'Query malformed'
            else:
                c.queryresults = [('p', 'o'), (1, 2), (3, 4), (4,3)]

        return render('package/sparql.html')

    def sparql_config(self, id):
        # using default functionality
        template = self.read(id)

        #check if metadada info exists and add it otherwise
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author}
        package_info = get_action('package_show')(context, {'id': c.pkg.id})

        #sparql_config functionality

        c.warningmessage = None
        c.successmessage = None
        c.globalendpointselected = False
        if self.packageendpoint and self.packageendpoint.isglobal:
            if self.packageendpoint.isdataallowed and self.packageendpoint.isenabled:
                globalendpoint = self.packageendpoint
                c.globalendpoint = True
                c.globalendpointselected = True
            else:
                c.warningmessage = "Sorry but global endpoint is now disabled, you can setup a new endpoint in this form."
                pass
        else:
            globalendpoint = model.Session.query(SparqlEndpoint).filter_by(isglobal=True, isenabled=True, isdataallowed=True).first()
            c.globalendpoint = True if globalendpoint else False

        c.storeconfigform = {}

        conf_file = ConfigParser.ConfigParser()
        conf_file.read(os.environ['CKAN_CONFIG'])

        # Check if there is any endpoint already selected, and don't show anything if it doesn't or if it is global endpoint
        # (Because it's not allowed to update global endpoint in this view)
        c.storeconfigform['endpoint_name'] = self.packageendpoint.name if (self.packageendpoint and not c.globalendpointselected) else id
        c.storeconfigform['endpoint_sparqlurl'] = self.packageendpoint.sparqlurl if (self.packageendpoint and not c.globalendpointselected) else ''
        c.storeconfigform['endpoint_sparulurl'] = self.packageendpoint.sparulurl if (self.packageendpoint and not c.globalendpointselected) else ''
        c.storeconfigform['endpoint_graph'] = self.packageendpoint.graph if (self.packageendpoint and not c.globalendpointselected) else request.url.replace('/edit/sparql', '')
        c.storeconfigform['endpoint_endpointtype'] = self.packageendpoint.storetype if (self.packageendpoint and not c.globalendpointselected) else 'virtuoso'
        c.storeconfigform['endpoint_user'] = self.packageendpoint.username if (self.packageendpoint and not c.globalendpointselected) else None
        c.storeconfigform['endpoint_passwd'] = self.packageendpoint.passwd if (self.packageendpoint and not c.globalendpointselected) else None
        c.storeconfigform['endpoint_enabled'] = self.packageendpoint.isenabled if (self.packageendpoint and not c.globalendpointselected) else None
        c.storeconfigform['endpoint_authrequired'] = self.packageendpoint.isauthrequired if (self.packageendpoint and not c.globalendpointselected) else False

        c.endpointtypes = ENDPOINT_TYPES

        if 'save' in request.params:
            # It's POST call after form
            packagedb = model.Session.query(Package).filter_by(name=id).first()

            if 'globalendpoint' in request.params.keys() and request.params['globalendpoint'] == 'global' and globalendpoint:
                if not c.globalendpointselected:
                    # It's not already selected
                    log.info('[' + id + '] Selecting global as endpoint...')
                    packagedb.endpoints = [globalendpoint]
                    if self.packageendpoint:
                        # There is already one selected, so remove it from endpoint list
                        log.info('[' + id + '] Removing existing -custom- endpoint to replace it with global one...')
                        model.Session.delete(self.packageendpoint)
                    model.Session.commit()
                    c.successmessage = "Global endpoint succesfully selected"
                else:
                    log.info('[' + id + '] No changes, global was already selected')
                    c.warningmessage = "No changes to do, global was already selected"
                c.globalendpointselected = True
            else:
                errors = False
                for field, value in request.params.items():
                    if not value and field not in ['user', 'passwd', 'globalendpoint']:
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
                        'isglobal': False,
                        'isdataallowed': False,
                        'isenabled': c.storeconfigform['endpoint_enabled'] if (self.packageendpoint and not c.globalendpointselected) else True
                    }

                    if self.packageendpoint and not c.globalendpointselected:
                        if dict((name, getattr(self.packageendpoint, name)) for name in dir(self.packageendpoint) if name in datadict.keys()) != datadict:
                            log.info('[' + id + '] Updating endpoint in database...')
                            self.packageendpointquery.update(datadict, synchronize_session='fetch')
                            c.storeconfigform['endpoint_enabled'] = True
                            c.successmessage = "Endpoint succesfully updated"
                        else:
                            log.info('[' + id + '] No changes')
                            c.warningmessage = "No changes to do"
                    else:
                        log.info('[' + id + '] Creating new endpoint in database...')
                        endpointdb = SparqlEndpoint(datadict)
                        model.Session.add(endpointdb)
                        packagedb.endpoints = [endpointdb]
                        c.storeconfigform['endpoint_enabled'] = True
                        c.successmessage = "Endpoint succesfully created"
                    model.Session.commit()
                c.globalendpointselected = False

        elif 'enable' in request.params and not c.globalendpointselected:
            if self.packageendpoint:
                self.packageendpoint.isenabled = True
                c.storeconfigform['endpoint_enabled'] = True
                log.info('[' + id + '] Enabling rdf store...')
                model.Session.commit()
                c.successmessage = "Endpoint succesfully enabled"

        elif 'disable' in request.params and not c.globalendpointselected:
            if self.packageendpoint:
                self.packageendpoint.isenabled = False
                c.storeconfigform['endpoint_enabled'] = False
                log.info('[' + id + '] Disabling rdf store...')
                model.Session.commit()
                c.successmessage = "Endpoint succesfully disabled"

        return render('package/config_sparql.html')


class SparqlGuiController(BaseController):
    # Check if the user is admin (based on CKAN's AdminController)
    def __before__(self, action, **params):
        super(SparqlGuiController, self).__before__(action, **params)
        self.mainendpoint = model.Session.query(SparqlEndpoint).filter_by(isglobal=True, isenabled=True).first()
        if not self.mainendpoint:
            abort(404)

    def sparql_endpoint(self):
        print self.mainendpoint.sparqlurl
        c.resultformats = {'html': 'HTML'}

        if 'runquery' in request.params:
            errors = False
            #g = rdflib.ConjunctiveGraph('SPARQLStore')
            #g.open("
            # Run query
            
            if errors:
                c.error_message = 'Query malformed'
            else:
                c.queryresults = [('p', 'o'), (1, 2), (3, 4), (4,3)]
        
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
        c.warningmessage = None
        c.successmessage = None
        c.storeconfigform = {}

        globalendpointquery = model.Session.query(SparqlEndpoint).filter_by(isglobal=True)
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

        c.endpointtypes = ENDPOINT_TYPES
        
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
                        log.info('[GLOBAL] Updating endpoint in database...')
                        globalendpointquery.update(datadict)
                        c.successmessage = "Global endpoint succesfully updated"
                    else:
                        log.info('[GLOBAL] No changes')
                        c.warningmessage = "No changes to do"
                else:
                    log.info('[GLOBAL] Creating new endpoint in database...')
                    endpointdb = SparqlEndpoint(datadict)
                    model.Session.add(endpointdb)
                    c.successmessage = "Global endpoint succesfully created"

                model.Session.commit()

        elif 'enable' in request.params:
            if globalendpoint:
                globalendpointquery.update({'isenabled': True})
                c.storeconfigform['endpoint_enabled'] = True
                log.info('[GLOBAL] Enabling rdf store...')
                model.Session.commit()
                c.successmessage = "Global endpoint succesfully enabled"

        elif 'disable' in request.params:
            if globalendpoint:
                globalendpointquery.update({'isenabled': False})
                c.storeconfigform['endpoint_enabled'] = False
                log.info('[GLOBAL] Disabling rdf store...')
                model.Session.commit()
                c.successmessage = "Global endpoint succesfully disabled"

        return render('admin/admin_sparql.html')