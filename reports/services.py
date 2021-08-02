import psycopg2
import pygrametl
from pygrametl.datasources import SQLSource
from pygrametl.tables import Dimension, CachedDimension, SnowflakedDimension,\
    SlowlyChangingDimension, BulkFactTable, FactTable

import datetime
import sys
import time

class ETLHandler():
    ''' '''

    @classmethod
    def datehandling(cls, row, namemapping):

        date = pygrametl.getvalue(row, 'date', namemapping)
        year, month, day, hour, minute, second, weekday, dayinyear, dst = date.timetuple()
        isoyear, isoweek, isoweekday = date.isocalendar()

        row['day'] = day
        row['month'] = month
        row['year'] = year
        row['week'] = isoweek
        row['weekyear'] = isoweek
        row['id'] = dayinyear + 366 * (year - 1990) #Support dates from 1990
        return row

    @classmethod
    def start(cls):
        source_string = "host='localhost' dbname='rino' user='rino' password='rino'"
        source_conn = psycopg2.connect(source_string)

        dw_string = "host='localhost' dbname='rino' user='rino' password='rino'"
        dw_conn = psycopg2.connect(dw_string)

        dw_conn_wrapper = pygrametl.ConnectionWrapper(connection=dw_conn)

        #name_mapping = 'book', 'genre', 'city', 'timestamp', 'sale'
        query = '''
            SELECT 
                COUNT(p.subtype_id) AS amount, 
                DATE(r.date_radicated) AS date_radicated, 
                st.id AS subtype_id,
                st.name AS subtype_name,
                t.id AS type_id,
                t.name AS type_name
            FROM 
                pqrs_pqrscontent p INNER 
                JOIN correspondence_radicate r ON p.radicate_ptr_id = r.id
                JOIN pqrs_subtype st ON p.subtype_id = st.id
                JOIN pqrs_type t ON st.type_id = t.id
            GROUP BY
                r.date_radicated,
                st.id,
                st.name,
                t.id,
                t.name
            '''
        pqrs_source = SQLSource(connection=source_conn, query=query) #,names=name_mapping)

        subtype_dimension = CachedDimension(
            name='dw_subtype',
            key='id',
            attributes=['name', 'type_id', 'type_name'],
            lookupatts=['id'],
            prefill=True)

        datedim = CachedDimension(
            name='dw_date',
            key='id',
            attributes=['date', 'day', 'month', 'year', 'week', 'weekyear'],
            lookupatts=['date'],
            rowexpander=cls.datehandling)
               
        fact_table = FactTable(
            name='dw_pqrs',
            keyrefs=['subtype_id', 'date_id'],
            measures=['amount'])

        for row in pqrs_source:

            #cls.split_timestamp(row)
            row['subtype_id'] = subtype_dimension.ensure(row, {'id': 'subtype_id', 'name': 'subtype_name', 'type_id': 'type_id', 'type_name': 'type_name'})
            row['date_id'] = datedim.ensure(row, {'date':'date_radicated'})
            fact_table.insert(row, {'amount':'amount'})

        dw_conn_wrapper.commit()
        dw_conn_wrapper.close()
        source_conn.close()

