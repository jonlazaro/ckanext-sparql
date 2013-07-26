# -*- coding: utf8 -*- 

from ckan.lib.celery_app import celery
from logging import getLogger

from celery.schedules import crontab
from celery.task import periodic_task

from datetime import timedelta, datetime

from rdflib import Graph

import urlparse
import urllib
import urllib2
import requests
import json

import os
import ConfigParser



#Configuration load
config = ConfigParser.ConfigParser()
config.read(os.environ['CKAN_CONFIG'])

MAIN_SECTION = 'app:main'
PLUGIN_SECTION = 'plugin:sparql'

SITE_URL = config.get(MAIN_SECTION, 'ckan.site_url')
API_URL = urlparse.urljoin(SITE_URL, 'api/')
API_KEY = config.get(PLUGIN_SECTION, 'api_key')
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

def get_package_list():
    res = requests.post(
        API_URL + 'action/package_list', json.dumps({}),
        headers = {'Authorization': API_KEY,
                   'Content-Type': 'application/json'}
    )

    if res.status_code == 200:
        return json.loads(res.content)['result']
    else:
        print 'ckan failed to get package list, status_code (%s), error %s' % (res.status_code, res.content)
        return ()

@periodic_task(run_every=periodicity)
def dataset_rdf_crawler():
    g = Graph()
    try:
        for package in get_package_list():
            request = urllib2.Request(urlparse.urljoin(DATASET_URL, package), headers={"Accept" : "application/rdf+xml"})
            g.parse(data=urllib2.urlopen(request).read())
            
            # [TODO] UPDATE SPARQL ENDPOINT WITH GRAPH!!!       
    except Exception:
        print 'CKAN server not running'
