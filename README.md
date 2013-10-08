ckanext-sparql
==============

SPARQL edpoint support for CKAN.

Tested with CKAN 1.8

 Installation
--------------

**Install plugin**

    python setup.py install
    
**Update CKAN development.ini file to load the plugin**

    ckan.plugins = stats sparql
    
**Check that CKAN libraries are installed**

    cd src/ckan
    python setup.py install

**Initialize new tables on CKAN database (Change user & pass)**

    python ckanext/sparql/sparql_model/initDB.py
    
**Add plugin configuration variables to CKAN development.ini**

Append this configuration snippet to the file. Do not forget to **change the admin API** key with yours.

	[plugin:sparql]
	# change this API key
	api_key = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    
	#run every s seconds, for debugging purposes
	#run_every = 30

	#sparql task cron
	cron_hour = 03
	cron_minute = 00
    
**Apply patch to CKAN code for adding periodic task support to paster launcher**

Copy patch content from https://gist.github.com/4547407 to a file named *beat_support.patch*
and execute next line on CKAN source directory

    git apply beat_support.patch
    
**Celery task queue initialization**
This plugin uses Celery (http://celeryproject.org/) for task queueing. 

Start the CKAN instance

    paster serve development.ini
    
Start the Celery server

    paster celeryd run beat
