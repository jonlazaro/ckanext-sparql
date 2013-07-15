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

    python ckanext/metadata/model/initDB.py
