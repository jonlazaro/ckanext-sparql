import model
from sqlalchemy import create_engine

USER = 'ckanuser'
PASS = 'pass'

alchemyurl = 'postgresql://%s:%s@localhost/ckantest' % (USER, PASS)

print 'Creating table for SPARQL endpoint storage'
engine = create_engine(alchemyurl, echo=True)
model.metadata.drop_all(engine)
model.metadata.create_all(engine)
