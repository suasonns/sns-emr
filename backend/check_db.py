from app.core.database import engine

with engine.connect() as c:
    print("DB:", c.exec_driver_sql("select current_database()").scalar())
    print("Port:", c.exec_driver_sql("show port").scalar())
    print("User:", c.exec_driver_sql("select current_user").scalar())
    print(
        "doc_table:",
        c.exec_driver_sql("select to_regclass('public.document_records')").scalar(),
    )
