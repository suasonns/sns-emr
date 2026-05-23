from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base
from app.db.session import engine  # adjust if your engine import differs

metadata = MetaData()
metadata.reflect(bind=engine, schema="public")

AutomapBase = automap_base(metadata=metadata)
AutomapBase.prepare()

# Now you can access tables as:
# AutomapBase.classes.document_records
# AutomapBase.classes.document_notifications
# AutomapBase.classes.patients
