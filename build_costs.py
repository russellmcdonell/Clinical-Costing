
# pylint: disable=line-too-long, broad-exception-caught
'''
The build script adjusts the general_ledger cost for cost based feeder data then
simplifies the general_ledger_costs by mapping, grouping and folding.

    SYNOPSIS:
    $ python build.py hospital_code model_code run_code
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
Then assemble the build the cost data.
'''

# pylint: disable=invalid-name, bare-except, pointless-string-statement, unspecified-encoding

import sys
import argparse
import logging
import pandas as pd
from sqlalchemy import text, delete
import functions as f
import data as d


if __name__ == '__main__':
    '''
    The main code
    Start by parsing the command line arguements and setting up logging.
    Then check that the hospital_code, model_code and run_code are valid.
    Then adjust the General Ledger costs for any cost based feeder data.
    Then simplify the General Ledger costs by mapping, folding and grouping.
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
    f.addCommonArguments(parser)      # Add the common command line arguments
    args = parser.parse_args()

    # Parse the command line options
    args = parser.parse_args()
    d.hospital_code = args.hospital_code
    d.model_code = args.model_code
    d.run_code = args.run_code
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
    whereRun = 'hospital_code = "' + d.hospital_code + '" AND run_code = "' + d.run_code + '"'
    whereModel = 'hospital_code = "' + d.hospital_code + '" AND model_code = "' + d.model_code + '"'
    whereHospital = 'hospital_code = "' + d.hospital_code + '"'

    # Delete any old data
    with d.Session() as session:
        session.execute(delete(d.metadata.tables['general_ledger_adjusted']).where(text(where)))
        session.execute(delete(d.metadata.tables['general_ledger_mapped']).where(text(where)))
        session.execute(delete(d.metadata.tables['general_ledger_built']).where(text(where)))
        session.commit()

    # Start by reading in the General Ledger costs.
    selectText = 'SELECT * FROM general_ledger_costs WHERE ' + whereRun
    glCosts_df = pd.read_sql_query(text(selectText), d.engine.connect())
    glCosts_df.insert(2, 'model_code', d.model_code)
    print(f"general_ledger_costs: ${glCosts_df['cost'].sum():.2f}")

    # Then adjust for any cost based feeder costs
    selectText = 'SELECT * FROM feeders WHERE ' + whereHospital
    feeders_df = pd.read_sql_query(text(selectText), d.engine.connect())
    selectText = 'SELECT * FROM feeder_model WHERE ' + whereModel
    feederAccounts_df = pd.read_sql_query(text(selectText), d.engine.connect())
    feederAccounts = {}
    for row in feederAccounts_df.itertuples():
        feeder_code = row.feeder_code
        feederAccounts[feeder_code] = {}
        feederAccounts[feeder_code]['new_department_code'] = row.new_department_code
        feederAccounts[feeder_code]['new_cost_type_code'] = row. new_cost_type_code
    selectText = 'SELECT * FROM itemized_costs WHERE ' + whereRun
    items_df = pd.read_sql_query(text(selectText), d.engine.connect())
    items_df = items_df.drop(columns=['hospital_code', 'run_code', 'who', 'invoice_no', 'invoice_line_no', 'service_code', 'episode_no', 'item_date', 'what'])
    items_df = items_df.groupby(['feeder_code', 'department_code', 'cost_type_code']).sum('amount')
    for groupTuple in items_df.index:
        feeder_code, department_code, cost_type_code = groupTuple
        if feeder_code not in feederAccounts:           # Some feeders are not in this model
            continue
        # Check that this is a cost based feeder
        if feeders_df[(feeders_df['feeder_code'] == feeder_code)]['feeder_type_code'].item() != 'C':
            continue
        amount = items_df.loc[groupTuple]['amount']
        new_department_code = feederAccounts[feeder_code]['new_department_code']
        new_cost_type_code = feederAccounts[feeder_code]['new_cost_type_code']
        glCosts_df = f.moveCosts(department_code, cost_type_code, amount, new_department_code, new_cost_type_code, 'A', glCosts_df)

    # Save the adjusted costs
    glCosts_df = glCosts_df[glCosts_df['cost'] != 0.0]
    glCosts_df.to_sql('general_ledger_adjusted', d.engine, if_exists='append', index=False)
    print(f"general_ledger_adjusted: ${glCosts_df['cost'].sum():.2f}")

    # Then do any General Ledger Run Adjustments
    selectText = 'SELECT * FROM general_ledger_run_adjustments WHERE ' + whereRun
    glAdjust_df = pd.read_sql_query(text(selectText), d.engine.connect())
    glCosts_df = f.generalLedgerAdjustOrMap(glAdjust_df, glCosts_df)

    # Then do any General Gedger Mappings
    selectText = 'SELECT * FROM general_ledger_mapping WHERE ' + whereModel
    generalLedgerMapping_df = pd.read_sql_query(text(selectText), d.engine.connect())
    generalLedgerMapping_df.sort_values(by='mapping_order', inplace=True, ascending=True)
    glCosts_df = f.generalLedgerAdjustOrMap(generalLedgerMapping_df, glCosts_df)

    # Save the mapped costs
    glCosts_df = glCosts_df[glCosts_df['cost'] != 0.0]
    glCosts_df.to_sql('general_ledger_mapped', d.engine, if_exists='append', index=False)
    print(f"general_ledger_mapped: ${glCosts_df['cost'].sum():.2f}")

    # Next do any General Ledger Grouping - starting with department grouping
    selectText = 'SELECT * FROM department_grouping WHERE ' + whereModel
    departmentGrouping_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for groupingRow in departmentGrouping_df.itertuples():
        from_department_code = groupingRow.from_department_code
        to_department_code = groupingRow.to_department_code
        glCostsTmp_df = glCosts_df[glCosts_df['department_code'] == from_department_code].copy()
        if len(glCostsTmp_df.index) == 0:
            continue            # No costs for this department in the General Ledger
        for glTmpRow in glCostsTmp_df.itertuples():
            from_cost_type_code = glTmpRow.cost_type_code
            to_cost_type_code = from_cost_type_code
            amount = glTmpRow.cost
            glCosts_df = f.moveCosts(from_department_code, from_cost_type_code, amount, to_department_code, to_cost_type_code, 'A', glCosts_df)

    # Then cost type with in department grouping
    preservedCostTypes = set()
    selectText = 'SELECT * FROM department_cost_type_grouping WHERE ' + whereModel
    departmentCostTypeGrouping_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for groupingRow in departmentCostTypeGrouping_df.itertuples():
        from_department_code = groupingRow.department_code
        to_department_code = from_department_code
        from_cost_type_code = groupingRow.from_cost_type_code
        to_cost_type_code = groupingRow.to_cost_type_code
        preservedCostTypes.add(to_cost_type_code)
        fromCosts_df = glCosts_df[(glCosts_df['department_code'] == from_department_code) & (glCosts_df['cost_type_code'] == from_cost_type_code)]
        if len(fromCosts_df.index) == 0:        # None of this cost in the General Ledger
            continue
        amount = fromCosts_df['cost'].item()
        glCosts_df = f.moveCosts(from_department_code, from_cost_type_code, amount, to_department_code, to_cost_type_code, 'A', glCosts_df)

    # Then simplify the cost types with cost type grouping
    selectText = 'SELECT * FROM cost_type_grouping WHERE ' + whereModel
    costTypeGrouping_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for groupingRow in costTypeGrouping_df.itertuples():
        from_cost_type_code = groupingRow.from_cost_type_code
        to_cost_type_code = groupingRow.to_cost_type_code
        preservedCostTypes.add(to_cost_type_code)
        glCostsTmp_df = glCosts_df[glCosts_df['cost_type_code'] == from_cost_type_code].copy()
        if len(glCostsTmp_df.index) == 0:
            continue        # No costs of this cost type in the General Ledger
        for glTmpRow in glCostsTmp_df.itertuples():
            from_department_code = glTmpRow.department_code
            to_department_code = from_department_code
            amount = glTmpRow.cost
            glCosts_df = f.moveCosts(from_department_code, from_cost_type_code, amount, to_department_code, to_cost_type_code, 'A', glCosts_df)

    # Finally, group all other cost types into 'other'
    glCostsTmp_df = glCosts_df[~glCosts_df['cost_type_code'].isin(preservedCostTypes)].copy()
    if len(glCostsTmp_df.index) != 0:
        for glTmpRow in glCostsTmp_df.itertuples():
            from_department_code = glTmpRow.department_code
            to_department_code = from_department_code
            from_cost_type_code = glTmpRow.cost_type_code
            amount = glTmpRow.cost
            glCosts_df = f.moveCosts(from_department_code, from_cost_type_code, amount, to_department_code, 'other', 'A', glCosts_df)

    # Save the built costs
    glCosts_df = glCosts_df[glCosts_df['cost'] != 0.0]
    glCosts_df.to_sql('general_ledger_built', d.engine, if_exists='append', index=False)
    print(f"general_ledger_built: ${glCosts_df['cost'].sum():.2f}")
