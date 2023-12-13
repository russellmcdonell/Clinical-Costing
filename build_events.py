
# pylint: disable=line-too-long, broad-exception-caught
'''
The build_events script builds events from non-cost based feeders and Patient Activity.

    SYNOPSIS:
    $ python build_event.py hospital_code model_code run_code
        [-i|--iterate]
        [-C configDir|--configDir=configDir] [-c configFile|--configFile=configFile]
        [-D DatabaseType|--DatabaseType=DatabaseType]
        [-s server|--server=server]
        [-u username|--username=username] [-p password|--password=password]
        [-d databaseName|--databaseName=databaseName]
        [-v loggingLevel|--verbose=logingLevel]
        [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]
<br/>

    REQUIRED
    hospital_code
    The hospital code for the hospital whose clinical costing data is being assembled.

    model_code
    The model code for the clinical costing model that is being used to assemble the clinical costing data.

    run_code
    The run code for the source data being used to assemble the clinical costing data for this hospital.


    OPTIONS
    -i|--iterate
    Use the iteration model for the disbursement

    -C configDir|--configDir=configDir
    The directory containing the database connection configuration file (default='databaseConfig')

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
Then build the events.
'''

# pylint: disable=invalid-name, bare-except, pointless-string-statement, unspecified-encoding

import sys
import argparse
import logging
import pandas as pd
from sqlalchemy import text, delete
import functions as f
import build_events_functions as bf
import data as d


if __name__ == '__main__':
    '''
    The main code
    Start by parsing the command line arguements and setting up logging.
    Then check that the hospital_code, model_code and run_code are valid.
    Then build the event and distribute the disbursed general ledger costs across those events.
    '''

    # Save the program name
    progName = sys.argv[0]
    progName = progName[0:-3]        # Strip off the .py ending

    # Set the options
    parser = argparse.ArgumentParser(description='Load a Clinical Costing Model')
    parser.add_argument('hospital_code',
                        help='The hospital code for the hospital whose clinical costing data is being assembled.')
    parser.add_argument('model_code',
                        help='The model code for the clinical costing model that is being used to assemble the clinical costing data.')
    parser.add_argument('run_code',
                        help='The run code for the source data being used to assemble the clinical costing data for this hospital.')
    parser.add_argument('-i', '--iterate', dest='useIteration', action='store_true',
                        help='Use the iteration model for the disbursement.')
    f.addCommonArguments(parser)      # Add the common command line arguments
    args = parser.parse_args()

    # Parse the command line options
    args = parser.parse_args()
    d.hospital_code = args.hospital_code
    d.model_code = args.model_code
    d.run_code = args.run_code
    useIteration = args.useIteration
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

    # Check that the hospital_code is valid
    hospitals_df = pd.read_sql_query(text('SELECT hospital_code FROM hospitals'), d.engine.connect())
    hospitals = hospitals_df.values.tolist()      # convert rows/columns to a list of lists (will be [[hospital_code]] )
    if not [d.hospital_code] in hospitals:
        logging.critical('hospital code (%s) no in table "hospitals"', d.hospital_code)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Check that the model_code is valid
    models_df = pd.read_sql_query(text('SELECT model_code FROM models'), d.engine.connect())
    models = models_df.values.tolist()      # convert rows/columns to a list of lists (will be [[model_code]] )
    if not [d.model_code] in models:
        logging.critical('model code (%s) no in table "models"', d.model_code)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Check that the run_code is valid
    selectText = 'SELECT run_code FROM clinical_costing_runs WHERE hospital_code = "' + d.hospital_code + '"'
    runs_df = pd.read_sql_query(text(selectText), d.engine.connect())
    runs = runs_df.values.tolist()      # convert rows/columns to a list of lists (will be [[run_code]] )
    if not [d.run_code] in runs:
        logging.critical('run code (%s) no in table "clinical_costing_runs"', d.run_code)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Build the 'where' clauses
    where = 'hospital_code = "' + d.hospital_code + '" AND model_code = "' + d.model_code + '" AND run_code = "' + d.run_code + '"'
    bf.SQLwhere = where
    whereRun = 'hospital_code = "' + d.hospital_code + '" AND run_code = "' + d.run_code + '"'
    bf.SQLwhereRun = whereRun
    whereModel = 'hospital_code = "' + d.hospital_code + '" AND model_code = "' + d.model_code + '"'
    bf.SQLwhereModel = whereModel
    whereHospital = 'hospital_code = "' + d.hospital_code + '"'
    bf.SQLwhereHospital = whereHospital

    # Delete any old data
    with d.Session() as session:
        session.execute(delete(d.metadata.tables['events']).where(text(where)))
        session.commit()

    # Build the events from the non-cost based feeder data
    selectText = 'SELECT feeder_code FROM feeders WHERE ' + whereHospital + ' AND feeder_type_code != "C"'
    feeders_df = pd.read_sql_query(text(selectText), d.engine.connect())
    selectText = f'SELECT hospital_code, run_code, "{d.model_code}" as model_code, feeder_code as event_code, '
    selectText += 'feeder_code as event_attribute_code, service_code, episode_no, invoice_line_no as event_seq, '
    selectText += 'invoice_no as event_what, feeder_code as distribution_code, 1.0 as event_weight '
    selectText += 'FROM itemized_costs WHERE ' + bf.SQLwhereRun
    for row in feeders_df.itertuples():
        feeder_code = row.feeder_code
        thisSelectText = selectText + f' AND feeder_code = "{feeder_code}"'
        events_df = pd.read_sql_query(text(thisSelectText), d.engine.connect())
        events_df.to_sql('events', d.engine, if_exists='append', index=False)

    # Cache event_codes, event_attributes, distribution_codes, ward_codes and clinic_codes
    # (We may have to build a new distribution code)
    d.codeTables['event_codes'] = {}
    selectText = 'SELECT event_code, event_description FROM event_codes WHERE ' + whereModel
    eventCodes_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in eventCodes_df.itertuples():
        d.codeTables['event_codes'][row.event_code] = row.event_description
    d.codeTables['event_attribute_codes'] = {}
    selectText = 'SELECT event_attribute_code, event_attribute_description FROM event_attribute_codes WHERE ' + whereModel
    eventAttributeCodes_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in eventAttributeCodes_df.itertuples():
        d.codeTables['event_attribute_codes'][row.event_attribute_code] = row.event_attribute_description
    d.codeTables['distribution_codes'] = {}
    selectText = 'SELECT distribution_code, distribution_description FROM distribution_codes WHERE ' + whereModel
    distributionCodes_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in distributionCodes_df.itertuples():
        d.codeTables['distribution_codes'][row.distribution_code] = row.distribution_description
    d.codeTables['ward_codes'] = {}
    selectText = 'SELECT ward_code, ward_description FROM wards WHERE ' + whereHospital
    wardCodes_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in wardCodes_df.itertuples():
        d.codeTables['ward_codes'][row.ward_code] = row.ward_description
    d.codeTables['clinic_codes'] = {}
    selectText = 'SELECT clinic_code, clinic_description FROM clinics WHERE ' + whereHospital
    clinicCodes_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in clinicCodes_df.itertuples():
        d.codeTables['clinic_codes'][row.clinic_code] = row.clinic_description

    # Then build the events from the Patient Activity data
    selectText = 'SELECT * FROM event_codes WHERE ' + whereModel
    eventCodes_df = pd.read_sql_query(text(selectText), d.engine.connect())
    selectText = 'SELECT * FROM event_attributes WHERE ' + whereModel
    eventAttributes_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in eventAttributes_df.itertuples():
        eventCode = row.event_code
        eventAttribute = row.event_attribute_code
        eventSubroutine = row.event_subroutine_name
        eventWhat = row.event_what
        eventWhere = row.event_where
        eventBase = row.event_attribute_base
        eventWeight = row.event_attribute_weight
        bf.buildEvent(eventSubroutine, eventCode, eventAttribute, eventWhat, eventWhere, eventBase, eventWeight)
