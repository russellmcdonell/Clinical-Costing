
# pylint: disable=line-too-long, broad-exception-caught
'''
The distribute_costs script distributes cost from direct general_ledger accounts to events.

    SYNOPSIS:
    $ python distribute.py hospital_code model_code run_code
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
Then disburse the distributed costs data.
'''

# pylint: disable=invalid-name, bare-except, pointless-string-statement, unspecified-encoding

import sys
import argparse
import logging
import pandas as pd
from sqlalchemy import text, delete, insert
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
        session.execute(delete(d.metadata.tables['event_costs']).where(text(where)))
        session.commit()

    # Create the event_cost records from the invoice data
    # Process each cost based feeder
    selectText = 'SELECT feeder_code FROM feeders WHERE ' + whereHospital + ' AND feeder_type_code = "C"'
    feeders_df = pd.read_sql_query(text(selectText), d.engine.connect())
    selectText = f'SELECT hospital_code, run_code, "{d.model_code}" as model_code, feeder_code as event_code, '
    selectText += 'feeder_code as event_attribute_code, service_code, episode_no, invoice_line_no as event_seq, '
    selectText += 'department_code, cost_type_code, invoice_no as event_what, feeder_code as distribution_code, amount as cost '
    selectText += 'FROM itemized_costs WHERE ' + bf.SQLwhereRun
    for row in feeders_df.itertuples():
        feeder_code = row.feeder_code
        thisSelectText = selectText + f' AND feeder_code = "{feeder_code}"'
        eventCosts_df = pd.read_sql_query(text(thisSelectText), d.engine.connect())
        eventCosts_df.to_sql('event_costs', d.engine, if_exists='append', index=False)

    # Next read in the General Ledger 'as disbursed' costs, ready for distribution.
    selectText = 'SELECT * FROM general_ledger_disbursed WHERE ' + where
    glCosts_df = pd.read_sql_query(text(selectText), d.engine.connect())
    print(f"general_ledger_disbursed: ${glCosts_df['cost'].sum():.2f}")

    # Next read in the general_ledger_distribution which tells how to distribute those costs
    selectText = 'SELECT * FROM general_ledger_distribution WHERE ' + whereModel
    distribution_df = pd.read_sql_query(text(selectText), d.engine.connect())

    # And finally the event over which those costs will be distributed
    selectText = 'SELECT * FROM events WHERE ' + where
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())

    # Now create the event_cost records
    params = {}
    params['hospital_code'] = d.hospital_code
    params['run_code'] = d.run_code
    params['model_code'] = d.model_code
    for row in distribution_df.itertuples():
        department_code = row.department_code
        cost_type_code = row.cost_type_code
        account_df = glCosts_df[(glCosts_df['department_code'] == department_code) & (glCosts_df['cost_type_code'] == cost_type_code)]
        if len(account_df.index) == 0:
            logging.warning('No account [department_code(%s), cost_type_code(%s)] in general_ledger_disbursed', department_code, cost_type_code)
            continue
        distribution_code = row.distribution_code
        theseEvents_df = events_df[events_df['distribution_code'] == distribution_code]
        if len(theseEvents_df.index) == 0:
            logging.warning('No events for distribution_code(%s)', distribution_code)
            continue
        # Get the total weight and distribute this cost over this weight
        originalCost = account_df['cost'].item()
        params['department_code'] = department_code
        params['cost_type_code'] = cost_type_code
        params['distribution_code'] = distribution_code
        totalWeight = theseEvents_df['event_weight'].sum()
        with d.Session() as session:
            for eventRow in theseEvents_df.itertuples():
                fraction = eventRow.event_weight / totalWeight
                partCost = originalCost * fraction
                params['event_code'] = eventRow.event_code
                params['event_attribute_code'] = eventRow.event_attribute_code
                params['service_code'] = eventRow.service_code
                params['episode_no'] = eventRow.episode_no
                params['event_seq'] = eventRow.event_seq
                params['event_what'] = eventRow.event_what
                params['cost'] = float(partCost)
                session.execute(insert(d.metadata.tables['event_costs']).values(params))
            session.commit()
        glCosts_df.loc[(glCosts_df['department_code'] == department_code) & (glCosts_df['cost_type_code'] == cost_type_code), 'cost'] = 0.0

    # Save the undistributed costs
    glCosts_df = glCosts_df[glCosts_df['cost'] != 0.0]
    glCosts_df.to_sql('general_ledger_undistribute', d.engine, if_exists='append', index=False)
    print(f"general_ledger_undistributed: ${glCosts_df['cost'].sum():.2f}")
