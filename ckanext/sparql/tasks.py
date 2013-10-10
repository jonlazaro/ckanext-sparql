# -*- coding: utf8 -*-

from ckan.lib.celery_app import celery

from celery.schedules import crontab
from celery.task import periodic_task

from datetime import timedelta, datetime
from rdflib import Graph
from requests.auth import HTTPBasicAuth

import urlparse
import urllib2
import requests
import os
import ConfigParser

from utils import update_task_status, get_package_list, get_global_sparql_enpoint

#Configuration load
config = ConfigParser.ConfigParser()
config.read(os.environ['CKAN_CONFIG'])

MAIN_SECTION = 'app:main'
PLUGIN_SECTION = 'plugin:sparql'

SITE_URL = config.get(MAIN_SECTION, 'ckan.site_url')
CRON_HOUR = config.get(PLUGIN_SECTION, 'cron_hour')
CRON_MINUTE = config.get(PLUGIN_SECTION, 'cron_minute')
DATASET_URL = urlparse.urljoin(SITE_URL, 'dataset/')

try:
    RUN_EVERY = config.get(PLUGIN_SECTION, 'run_every')
except ConfigParser.NoOptionError:
    RUN_EVERY = None

if RUN_EVERY is not None:
    print 'Launching periodic tasks every %s seconds' % RUN_EVERY
    periodicity = timedelta(seconds=int(RUN_EVERY))
else:
    print 'Launching periodic task at %s:%s' % (CRON_HOUR, CRON_MINUTE)
    periodicity = crontab(hour=CRON_HOUR, minute=CRON_MINUTE)


def validate_rdf_data(data, data_format):
    g = Graph()
    g.parse(data=data, format=data_format)
    return g

def upload_rdf_data(graph, pkg_data):
    headers = {}
    success_codes = []

    triples = ''
    for s, p, o in graph.triples((None, None, None)):
        triple = "%s %s %s . " % (s.n3(), p.n3(), o.n3())
        triples += triple

    if pkg_data['storetype'] == 'virtuoso':
        query = 'INSERT IN GRAPH <%s> { %s }' % (pkg_data['graph'].encode('utf-8'), triples)
        headers = {'Content-type': 'application/sparql-query'}
        success_codes = [201]

    elif pkg_data['storetype'] == 'sparql11':
        query = 'INSERT DATA { GRAPH %s { %s } }' % (pkg_data['graph'].encode('utf-8'), triples)
        headers = {'Content-type': 'application/sparql-update', 'Connection': 'Keep-Alive'}
        success_codes = [200, 204]

    if pkg_data['isauthrequired']:
        r = requests.post(pkg_data['sparulurl'], data=query.encode('utf-8'), headers=headers, auth=HTTPBasicAuth(pkg_data['username'], pkg_data['passwd']))
    else:
        r = requests.post(pkg_data['sparulurl'], data=query.encode('utf-8'), headers=headers)

    if r.status_code not in success_codes:
        raise Exception("Insertion call failed")

@celery.task(name="upload_rdf")
def upload_rdf(pkg_data, data, data_format):
    # Task status: RUNNING
    task_info = {
        'entity_id': pkg_data['id'],
        'entity_type': u'package',
        'task_type': u'upload_rdf',
        'key': u'celery_task_status',
        'value': u'%s - %s' % ('RUNNING', unicode(upload_rdf.request.id)),
        'error': u'',
        'last_updated': datetime.now().isoformat()
    }
    update_task_status(task_info)

    graph = None
    try:
        graph = validate_rdf_data(data, data_format)
    except:
        # Task status: ERROR
        task_info = {
            'entity_id': pkg_data['id'],
            'entity_type': u'package',
            'task_type': u'upload_rdf',
            'key': u'celery_task_status',
            'value': u'%s - %s' % ('ERROR', unicode(upload_rdf.request.id)),
            'error': u'Uploaded data is not valid RDF or it\'s not in the given format (%s).' % data_format,
            'last_updated': datetime.now().isoformat()
        }
        update_task_status(task_info)
        return 0

    try:
        upload_rdf_data(graph, pkg_data)
    except Exception, e:
        # Task status: ERROR
        task_info = {
            'entity_id': pkg_data['id'],
            'entity_type': u'package',
            'task_type': u'upload_rdf',
            'key': u'celery_task_status',
            'value': u'%s - %s' % ('ERROR', unicode(upload_rdf.request.id)),
            'error': u'Could not upload RDF data. %s' % e,
            'last_updated': datetime.now().isoformat()
        }
        update_task_status(task_info)
        return 0

    # Task status: FINISHED
    task_info = {
        'entity_id': pkg_data['id'],
        'entity_type': u'package',
        'task_type': u'upload_rdf',
        'key': u'celery_task_status',
        'value': u'%s - %s' % ('FINISHED', unicode(upload_rdf.request.id)),
        'error': u'',
        'last_updated': datetime.now().isoformat()
    }
    update_task_status(task_info)
    return 1

@periodic_task(run_every=periodicity)
def dataset_rdf_crawler():
    # Task status: RUNNING
    task_info = {
        'entity_id': 'GLOBAL',
        'entity_type': u'package',
        'task_type': u'rdf_crawler',
        'key': u'celery_task_status',
        'value': u'%s - %s' % ('RUNNING', unicode(dataset_rdf_crawler.request.id)),
        'error': u'',
        'last_updated': datetime.now().isoformat()
    }
    update_task_status(task_info)

    try:
        crawl_and_upload_data()
    except Exception, e:
        # Task status: ERROR
        task_info = {
            'entity_id': 'GLOBAL',
            'entity_type': u'package',
            'task_type': u'rdf_crawler',
            'key': u'celery_task_status',
            'value': u'%s - %s' % ('ERROR', unicode(dataset_rdf_crawler.request.id)),
            'error': u'Error ocurred while crawling RDF data from CKAN. %s' % e,
            'last_updated': datetime.now().isoformat()
        }
        update_task_status(task_info)

def crawl_and_upload_data():
    g = Graph()
    sparql_endpoint = get_global_sparql_enpoint()

    if sparql_endpoint:
        for package in get_package_list():
            request = urllib2.Request(urlparse.urljoin(DATASET_URL, package), headers={"Accept" : "application/rdf+xml"})
            g.parse(data=urllib2.urlopen(request).read())
            upload_rdf_data(g, sparql_endpoint)
        # Task status: FINISHED
        task_info = {
            'entity_id': 'GLOBAL',
            'entity_type': u'package',
            'task_type': u'rdf_crawler',
            'key': u'celery_task_status',
            'value': u'%s - %s' % ('FINISHED', unicode(dataset_rdf_crawler.request.id)),
            'error': u'',
            'last_updated': datetime.now().isoformat()
        }
        update_task_status(task_info)
    else:
        # Task status: ERROR
        task_info = {
            'entity_id': 'GLOBAL',
            'entity_type': u'package',
            'task_type': u'rdf_crawler',
            'key': u'celery_task_status',
            'value': u'%s - %s' % ('ERROR', unicode(dataset_rdf_crawler.request.id)),
            'error': u'No global endpoint defined or not authorization to see its details.',
            'last_updated': datetime.now().isoformat()
        }
        update_task_status(task_info)
