
# pylint: disable=line-too-long, broad-exception-caught
'''
The load_model script loads the clinical costing model configuration data, for a specific costing model
into the Clinical Costing tables, from an Excel workbook

    SYNOPSIS
    $ python load_model.py
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
    The directory containing the Excel workbook containing the model to be loaded.

    -i inputWorkbook|--inputWorkbook=inputWorkbook
    The Excel workbook containing the model configuration data, for this hospital, to be loaded.

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
from sqlalchemy import text, select, insert, update
from openpyxl import load_workbook
import functions as f
import data as d


# Define the required worksheets and associated database tables
requiredSheets = {
    'mapping types': 'mapping_types',
    'general ledger mapping': 'general_ledger_mapping',
    'department grouping': 'department_grouping',
    'cost type grouping': 'cost_type_grouping',
    'department cost type grouping': 'department_cost_type_grouping',
    'event class codes': 'event_class_codes',
    'event cost type codes': 'event_cost_type_codes',
    'event cost sub type codes': 'event_cost_sub_type_codes',
    'event source codes': 'event_source_codes',
    'event codes': 'event_codes',
    'event attribute codes': 'event_attribute_codes',
    'general ledger attribute codes': 'general_ledger_attribute_codes',
    'general ledger attributes': 'general_ledger_attributes',
    'general ledger disbursement': 'general_ledger_disbursement',
    'general ledger distribution': 'general_ledger_distribution'
}

if __name__ == '__main__':
    '''
    The main code
    Start by parsing the command line arguements and setting up logging.
    Then check the Excel workbook - it should have one sheet for the hospital code/name, one sheet for the model code/name
    and one sheet for each model configuration table, in the Clinical Costing database.
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

    # Check if this is hospital code exists in the database
    selected = pd.read_sql_query(text('SELECT hospital_code FROM hospitals'), d.engine.connect())
    hospitals = selected.values.tolist()      # convert rows/columns to a list of lists (will be [[hospital_code]] )
    haveHospital = [hospital_code] in hospitals
    if not haveHospital:
        logging.critical('No hospital_code %s exists in the Clinical Costing database')
        logging.critical('Must load the hospital departments and cost types before you can model the hospitals costs')
        logging.shutdown()
        sys.exit(d.EX_DATAERR)

    # Check that the 'model' worksheet exits
    table_df = f.checkWorksheet(wb, 'model', 'models', [])

    # Get the model_code from the worksheet
    ws = wb['model']
    model_code = ws['A2'].value        # First (and only) model_code in the list

    # Check if this is a new model code, or upgraded configuration of an existing model
    selected = pd.read_sql_query(text('SELECT model_code FROM models'), d.engine.connect())
    models = selected.values.tolist()      # convert rows/columns to a list of lists (will be [[model_code]] )
    newModel = not [model_code] in models

    # Check the required configuration data worksheets
    sheet_table_df = {}
    for sheet, table in requiredSheets.items():
        sheet_table_df[sheet] = f.checkWorksheet(wb, sheet, table, ['hospital_code', 'model_code'])

    # If this is a new model, then add it to the table
    if newModel:
        table_df = table_df.truncate(after=0)       # We only want the first row
        table_df.to_sql('models', d.engine, if_exists='append', index=False)

    # Load the model configurations
    for sheet, table in requiredSheets.items():
        table_df = sheet_table_df[sheet]

        # Prepend the hospital code and the model code
        table_df.insert(0,'hospital_code', hospital_code)
        table_df.insert(0,'model_code', model_code)

        # For a new model, just append the data
        if  newModel:
            # Append the new data to the table
            table_df.to_sql(table, d.engine, if_exists='append', index=False)
        else:   # Process each row of the spreadsheet, doing an update or an append
                # [Deletes are not supported as they could break the referrential integrety of exising data]
            # Collect all the indexed columns - assume that there are foreign keys associated with these
            indexedColumns = []
            for index in d.metadata.tables[table].indexes:
                for col in index.columns:
                    if col.name not in indexedColumns:
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
                            logging.debug('Existing model update: updating table %s, with values %s, where %s', table, params, where)
                            session.execute(update(d.metadata.tables[table]).values(params).where(text(where)))
                            session.commit()
                    else:
                        logging.debug('New model: inserting into table %s value %s', table, params)
                        session.execute(insert(d.metadata.tables[table]).values(params))
                        session.commit()
