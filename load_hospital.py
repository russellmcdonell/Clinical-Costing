
# pylint: disable=line-too-long, broad-exception-caught
'''
The load_hospital script loads the configuration data for a hospital
into the Clinical Costing tables, from an Excel workbook.

    SYNOPSIS
    $ python load_hospital.py
        [-I inputDir|--inputDir=inputDir] [-i inputWorkbook|--inputWorkbook=inputWorkbook]
        [-C configDir|--configDir=configDir] [-c configFile|--configFile=configFile]
        [-D DatabaseType|--DatabaseType=DatabaseType]
        [-s server|--server=server]
        [-u username|--username=username] [-p password|--password=password]
        [-d databaseName|--databaseName=databaseName]
        [-v loggingLevel|--verbose=logingLevel]
        [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]
<br/>

    OPTIONS
    -I inputDir|--inputDir=inputDir
    The directory containing the Excel workbook containing the hospital configuration data to be loaded.

    -i inputWorkbook|--inputWorkbook=inputWorkbook
    The Excel workbook which contains the hospital configuration data to be loaded.

    -C configDir|--configDir=configDir
    The directory where the database connection configuration file can be found (default='databaseConfig')

    -c configFile|--configFile=configFile
    The database connection configuration file (default=clinical_costing.json) which has the default database values for each Database Type.
    These can be overwritten using command line options.

    -D DatabaseType|--DatabaseType=DatabaseType
    The type of database [choice:MSSQL/MySQL]

    -s server|--server=server]
    The address of the database server

    -u userName|--userName=userName]
    The user name require to access the database

    -p password|--userName=userName]
    The user password require to access the database

    -d databaseName|--databaseName=databaseName]
    The name of the database

    -v loggingLevel|--verbose=loggingLevel
    Set the level of logging that you want.

    -O logDir|--logDir=logDir
    The directory where the log file will be created.

    -o logfile|--logfile=logfile
    The name of a log file where you want all messages captured.


THE MAIN CODE
Start by parsing the command line arguements and setting up logging.
Connect to the database and read the configuration from an Excel workbook.
Then check that configuration and load the data.
'''

# pylint: disable=invalid-name, bare-except, pointless-string-statement, unspecified-encoding

import os
import sys
import argparse
import logging
import pandas as pd
from sqlalchemy import text, select, update, insert
from openpyxl import load_workbook
import functions as f
import data as d


# Define the required worksheets and associated database tables
requiredSheets = {
    'departments': 'departments',
    'cost types': 'cost_types',
    'services': 'services',
    'wards': 'wards',
    'theatres': 'theatres',
    'clinics': 'clinics',
    'clinicians': 'clinicians'
}

if __name__ == '__main__':
    '''
    The main code
    Start by parsing the command line arguements and setting up logging.
    Then check the Excel workbook - it should have one sheet for the hospital code/name
    and one sheet for each hospital configuration table, in the Clinical Costing database.
    And each sheet should have a header row with headings that match the names of the columns in the associated database table.
    '''

    # Save the program name
    progName = sys.argv[0]
    progName = progName[0:-3]        # Strip off the .py ending

    # Set the options
    parser = argparse.ArgumentParser(description='Load a Clinical Costing Model')
    parser.add_argument('-I', '--inputDir', dest='inputDir', default='.',
                        help='The directory containing the Excel workbook which contains the hospital patient activity data to be loaded.')
    parser.add_argument('-i', '--inputWorkbook', dest='inputWorkbook',
                        default='.', help='The name of the Excel workbook containing the hospital patient activity data to be loaded')
    f.addCommonArguments(parser)      # Add the common command line arguments
    args = parser.parse_args()

    # Parse the command line options
    args = parser.parse_args()
    inputDir = args.inputDir
    inputWorkbook = args.inputWorkbook
    configDir = args.configDir
    configFile = args.configFile
    DatabaseType = args.DatabaseType
    server = args.server
    username = args.username
    password = args.password
    databaseName = args.databaseName
    logDir = args.logDir
    logFile = args.logFile
    loggingLevel = args.verbose

    # Set up logging
    f.setupLogging(progName, logDir, logFile, loggingLevel)

    # Read in the configuration file - which must exist if required - and create the database engine
    f.createEngine(configDir, configFile, DatabaseType, server, username, password, databaseName)

    # Load the workbook
    wb = load_workbook(os.path.join(inputDir, inputWorkbook))

    # Check the 'hospital' worksheet
    table_df = f.checkWorksheet(wb, 'hospital', 'hospitals', [])

    # Get the hospital_code from the worksheet
    ws = wb['hospital']
    hospital_code = ws['A2'].value        # First (and only) hospital_code in the list

    # Check if this is a new hospital code, or upgraded configuration of an existing hospital
    hospitals_df = pd.read_sql_query(text('SELECT hospital_code FROM hospitals'), d.engine.connect())
    hospitals = hospitals_df.values.tolist()      # convert rows/columns to a list of lists (will be [[hospital_code]] )
    newHospital = not [hospital_code] in hospitals

    # Check the required configuration data worksheets
    sheet_tables_df = {}
    for sheet, table in requiredSheets.items():
        sheet_tables_df[sheet] = f.checkWorksheet(wb, sheet, table, ['hospital_code'])

    # If this is a new hospital, then add it to the table
    if newHospital:
        table_df = table_df.truncate(after=0)       # We only want the first row
        table_df.to_sql('hospitals', d.engine, if_exists='append', index=False)

    # Add this configuation data to the database
    for sheet, table in requiredSheets.items():
        table_df = sheet_tables_df[sheet]

        # Prepend the hospital code
        table_df.insert(0,'hospital_code', hospital_code)

        # For a new hospital, just append the data
        if  newHospital:
            # Append the new data to the table
            table_df.to_sql(table, d.engine, if_exists='append', index=False)
        else:   # Process each row of the spreadsheet, doing an update or an append
                # [Deletes are not supported as they could break the referrential integrety of exising data]
            # Collect all the indexed columns - assume that there are foreign keys associated with these
            indexedColumns = []
            for index in d.metadata.tables[table].indexes:
                for col in index.columns:
                    indexedColumns.append(col.name)
            # Process each row
            for row in table_df.itertuples(index=False):
                where = ''
                results = []
                # Build a where clause, based on the values of the primary key and indexed columns
                for col in indexedColumns:
                    if where != '':
                        where += ' AND '
                    where += col + ' = "' + getattr(row, col) + '"'
                for col in d.metadata.tables[table].primary_key.columns:
                    colName = col.name
                    if colName in indexedColumns:
                        continue
                    if where != '':
                        where += ' AND '
                    value = getattr(row, colName)
                    if isinstance(value, int) or isinstance(value, float):
                        where += colName + ' = ' + str(value)
                    elif isinstance(value, str):
                        where += colName + ' = "' + value + '"'
                    else:
                        where += colName + ' = "' + str(value) + '"'
                with d.Session() as session:
                    results = session.scalars(select(d.metadata.tables[table]).where(text(where))).all()
                # Assemble the parameters (values to be updated, or inserted)
                params = {}
                for col in d.metadata.tables[table].columns:
                    colName = col.name
                    if (len(results) > 0) and (colName in indexedColumns):
                        continue
                    params[colName] = getattr(row, colName)
                with d.Session() as session:
                    if (len(results) > 0):      # A row exists
                        if (len(params) > 0):       # Which has updatable columns (not part of primary key or foreign key)
                            logging.debug('Existing hospital update: updating table %s, with values %s, where %s', table, params, where)
                            session.execute(update(d.metadata.tables[table]).values(params).where(text(where)))
                            session.commit()
                    else:
                        logging.debug('New hospital: inserting into table %s value %s', table, params)
                        session.execute(insert(d.metadata.tables[table]).values(params))
                        session.commit()
