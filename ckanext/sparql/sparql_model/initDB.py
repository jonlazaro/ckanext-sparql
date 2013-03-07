import model
from sqlalchemy import create_engine

alchemyurl = 'postgresql://ckanuser:pass@localhost/ckantest'

print 'Creating table for SPARQL endpoint storage'
engine = create_engine(alchemyurl, echo=True)
model.metadata.drop_all(engine)
model.metadata.create_all(engine)
