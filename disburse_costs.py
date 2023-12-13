
# pylint: disable=line-too-long, broad-exception-caught
'''
The disburse script disburses cost from indirect general_ledger accounts.

    SYNOPSIS:
    $ python disburse.py hospital_code model_code run_code
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
Then disburse indirect costs.
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
    Then disburse any indirect cost accounts to direct cost accounts.
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
    whereRun = 'hospital_code = "' + d.hospital_code + '" AND run_code = "' + d.run_code + '"'
    whereModel = 'hospital_code = "' + d.hospital_code + '" AND model_code = "' + d.model_code + '"'
    whereHospital = 'hospital_code = "' + d.hospital_code + '"'

    # Delete any old data
    with d.Session() as session:
        session.execute(delete(d.metadata.tables['general_ledger_disbursed']).where(text(where)))
        session.commit()

    # Start by reading in the General Ledger 'as built' costs.
    selectText = 'SELECT * FROM general_ledger_built WHERE ' + where
    glCosts_df = pd.read_sql_query(text(selectText), d.engine.connect())
    print(f"general_ledger_built: ${glCosts_df['cost'].sum():.2f}")

    # Next, update any 'total*' general ledger attributes with the total cost for the matching department
    glTotalCosts_df = glCosts_df.groupby('department_code').sum('cost').reset_index()
    departments = glTotalCosts_df['department_code'].tolist()
    selectText = 'SELECT * FROM general_ledger_attributes WHERE ' + whereModel
    attributes_df = pd.read_sql_query(text(selectText), d.engine.connect())
    tmpAttributes_df = attributes_df[attributes_df['general_ledger_attribute_code'].str.startswith('total')].copy()
    for row in tmpAttributes_df.itertuples():
        department_code = row.department_code
        cost_type_code = row.cost_type_code
        attribute_code = row.general_ledger_attribute_code
        if department_code not in departments:
            attribute_weight = 0.0
        else:
            attribute_weight = glTotalCosts_df[glTotalCosts_df['department_code'] == department_code]['cost'].item()
        attributes_df.loc[(attributes_df['department_code'] == department_code) &
                      (attributes_df['cost_type_code'] == cost_type_code) & 
                      (attributes_df['general_ledger_attribute_code'] == attribute_code), ['general_ledger_attribute_weight']] = attribute_weight

    # Next apply any gl_attributes_run_adjustments
    selectText = 'SELECT * FROM gl_attributes_run_adjustments WHERE ' + whereRun
    adjustments_df = pd.read_sql_query(text(selectText), d.engine.connect())
    # We need to make sure that there aren't any attribute codes which aren't in the model
    attributes = attributes_df['general_ledger_attribute_code'].tolist()
    for row in adjustments_df.itertuples():
        department_code = row.department_code
        cost_type_code = row.cost_type_code
        attribute_code = row.general_ledger_attribute_code
        if attribute_code not in attributes:
            logging.warning('general_ledger_attribute_code(%s) in run adjustments is not in model(%s)', attribute_code, d.run_code)
            continue
        attribute_weight = row.general_ledger_attribute_weight
        thisAttribute_df = attributes_df.loc[(attributes_df['department_code'] == department_code) & 
                                             (attributes_df['cost_type_code'] == cost_type_code) & 
                                             (attributes_df['general_ledger_attribute_code'] == attribute_code)].copy()
        if len(thisAttribute_df.index) == 0:
            continue
        attributes_df.loc[(attributes_df['department_code'] == department_code) &
                      (attributes_df['cost_type_code'] == cost_type_code) & 
                      (attributes_df['general_ledger_attribute_code'] == attribute_code), ['general_ledger_attribute_weight']] = attribute_weight


    # Then read in the General Ledger Disbursement
    selectText = 'SELECT * FROM general_ledger_disbursement WHERE ' + whereModel
    disbursement_df = pd.read_sql_query(text(selectText), d.engine.connect())

    # Now workout the disbursment levels
    levels = {}
    targetLevels = {}
    indCosts = 0
    lastIndCosts = None
    for row in disbursement_df.itertuples():
        level = row.disbursement_level
        if level not in levels:
            levels[level] = []
        deptCode = row.department_code
        ctypeCode = row.cost_type_code
        attributeCode = row.general_ledger_attribute_code
        levels[level].append((deptCode, ctypeCode, attributeCode))
        targetLevels[(deptCode, ctypeCode)] = level
        indCost = glCosts_df[((glCosts_df['department_code'] == deptCode) & (glCosts_df['cost_type_code'] == ctypeCode))]
        if len(indCost.index) > 0:
            indCosts += indCost['cost'].item()
    print(f'Initial indirect costs: ${indCosts:.2f}')

    # Now disburse the indirect costs
    iterationNo = 1
    while indCosts > 0.05:       # Down to the last 5 cents
        for level in sorted(levels):        # Process each level in order (in case we are cascading)
            for deptCode, ctypeCode, attributeCode in levels[level]:
                indCost = glCosts_df[((glCosts_df['department_code'] == deptCode) & (glCosts_df['cost_type_code'] == ctypeCode))]
                if len(indCost.index) == 0:
                    continue
                thisIndCost = indCost['cost'].item()
                targetAccounts_df = attributes_df[attributes_df['general_ledger_attribute_code'] == attributeCode]
                # Check each account to see if it really is a target
                targetAccounts = []
                totalWeight = 0.0
                for row in targetAccounts_df.itertuples():
                    targetDept = row.department_code
                    targetCtypeCode = row.cost_type_code
                    if not useIteration:
                        if ((targetDept, targetCtypeCode)  in targetLevels) and (targetLevels[(targetDept, targetCtypeCode)] <= level):
                            continue
                    targetWeight = row.general_ledger_attribute_weight
                    if targetWeight < 0:
                        logging.critical('general_ledger_attribute_weights must not be negative:department_code(%s), cost_type_code(%s), general_ledger_attribute_weight(%s)',
                                         targetDept, targetCtypeCode, targetWeight)
                        logging.shutdown()
                        sys.exit(d.EX_CONFIG)
                    targetAccounts.append((targetDept, targetCtypeCode, targetWeight))
                    totalWeight += targetWeight
                if totalWeight == 0.0:
                    continue    # Nothing to distribute to
                for targetDept, targetCtypeCode, targetWeight in targetAccounts:
                    thisFraction = targetWeight / totalWeight
                    thisCost = thisIndCost * thisFraction
                    glCosts_df = f.moveCosts(deptCode, ctypeCode, thisCost, targetDept, targetCtypeCode, 'A', glCosts_df)

        # Compute the amount of remaining indirect costs
        indCosts = 0
        for row in disbursement_df.itertuples():
            deptCode = row.department_code
            ctypeCode = row.cost_type_code

            indCost = glCosts_df[((glCosts_df['department_code'] == deptCode) & (glCosts_df['cost_type_code'] == ctypeCode))]
            if len(indCost.index) > 0:
                indCosts += indCost['cost'].item()
        if useIteration:
            print(f'Remaining indirect costs (after iternation {iterationNo}): ${indCosts:.2f}')
            iterationNo += 1
            if lastIndCosts is None:
                lastIndCosts = indCosts
                continue
            if lastIndCosts == indCosts:
                logging.critical('Faulty iteration disbursement model - indirect costs remaining in indirect cost account')
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            lastIndCosts = indCosts
            continue
        break
    if not useIteration:
        print(f'Remaining indirect costs (after cascading): ${indCosts:.2f}')

    # Save the disbursed costs
    glCosts_df = glCosts_df[glCosts_df['cost'] != 0.0]
    glCosts_df.to_sql('general_ledger_disbursed', d.engine, if_exists='append', index=False)
    print(f"general_ledger_disbursed: ${glCosts_df['cost'].sum():.2f}")
