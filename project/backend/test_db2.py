import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='journeys' AND TABLE_SCHEMA='dbo'"))
    for row in res:
        print(row)
