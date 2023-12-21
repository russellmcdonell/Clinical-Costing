'''
The common functions for the Clinical Costing system.
'''

# pylint: disable=invalid-name, line-too-long, broad-exception-caught, unused-variable, superfluous-parens

import os
import sys
import logging
import collections
import json
import decimal
import pandas as pd
from sqlalchemy import create_engine, MetaData, text, select, insert, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy_utils import database_exists
import data as d


def addCommonArguments(parser):
    '''
    Add the common command line arguments
    '''
    parser.add_argument('-C', '--configDir', dest='configDir', default='databaseConfig',
                        help='The name of the directory containing the database connection configuration file (default=config)')
    parser.add_argument('-c', '--configFile', dest='configFile', default='clinical_costing.json',
                        help='The name of the configuration file (default clinical_costing.json)')
    parser.add_argument('-D', '--DatabaseType', dest='DatabaseType', choices=['MSSQL', 'MySQL'],
                        help='The Database Type [choices: MSSQL/MySQL]')
    parser.add_argument('-s', '--server', dest='server', help='The address of the database server')
    parser.add_argument('-u', '--username', dest='username', help='The user required to access the database')
    parser.add_argument('-p', '--password', dest='password', help='The user password required to access the database')
    parser.add_argument('-d', '--databaseName', dest='databaseName', help='The name of the database')
    parser.add_argument ('-v', '--verbose', dest='verbose', type=int, choices=range(0,5), help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument ('-L', '--logDir', dest='logDir', default='.', metavar='logDir', help='The name of the directory where the logging file will be created')
    parser.add_argument ('-l', '--logFile', dest='logFile', metavar='logfile', help='The name of a logging file')
    return


def setupLogging(progName, logDir, logFile, loggingLevel):
    '''
    Set up the logging
    '''
    logging_levels = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARNING, 3:logging.INFO, 4:logging.DEBUG}
    logfmt = progName + ' [%(asctime)s]: %(message)s'
    if loggingLevel is not None:    # Change the logging level from "WARN" if the -v vebose option is specified
        if logFile is not None:        # and send it to a file if the -o logfile option is specified
            with open(os.path.join(logDir, logFile), 'wt', encoding='utf-8', newline='') as logOutput:
                pass
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel], filename=os.path.join(logDir, logFile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
    else:
        if logFile is not None:        # send the default (WARN) logging to a file if the -o logfile option is specified
            with open(os.path.join(logDir, logFile), 'wt', encoding='utf-8', newline='') as logOutput:
                pass
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', filename=os.path.join(logDir, logFile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')

    # Set the SQLAlchemy logging level
    if loggingLevel is not None:
        logging.getLogger('sqlalchemy.engine').setLevel(logging_levels[loggingLevel])
    else:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)
    return


def createEngine(configDir, configFile, DatabaseType, server, username, password, databaseName):
    '''
    Parse the config file and create the database engine and session maker
    '''
    config = {}                 # The configuration data
    try:
        with open(os.path.join(configDir, configFile), 'rt', newline='', encoding='utf-8') as configSource:
            config = json.load(configSource, object_pairs_hook=collections.OrderedDict)
    except IOError:
        logging.critical('configFile (%s/%s) failed to load', configDir, configFile)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Check that we have a databaseName if we have a databaseType
    if DatabaseType not in config:
        logging.critical('DatabaseType(%s) not found in configuraton file(%s)', DatabaseType, configFile)
        logging.shutdown()
        sys.exit(d.EX_USAGE)
    if 'connectionString' not in config[DatabaseType]:
        logging.critical('No %s connectionString defined in configuration file(SQLAlchemyDB.json)', DatabaseType)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    connectionString = config[DatabaseType]['connectionString']
    if ('username' in config[DatabaseType]) and (username is None):
        username = config[DatabaseType]['username']
    if ('password' in config[DatabaseType]) and (password is None):
        password = config[DatabaseType]['password']
    if ('server' in config[DatabaseType]) and (server is None):
        server = config[DatabaseType]['server']
    if ('databaseName' in config[DatabaseType]) and (databaseName is None):
        databaseName = config[DatabaseType]['databaseName']

    # Check that we have all the required paramaters
    if username is None:
        logging.critical('Missing definition for "username"')
        logging.shutdown()
        sys.exit(d.EX_USAGE)
    if password is None:
        logging.critical('Missing definition for "password"')
        logging.shutdown()
        sys.exit(d.EX_USAGE)
    if server is None:
        logging.critical('Missing definition for "server"')
        logging.shutdown()
        sys.exit(d.EX_USAGE)
    if databaseName is None:
        logging.critical('Missing definition for "databaseName"')
        logging.shutdown()
        sys.exit(d.EX_USAGE)
    connectionString = connectionString.format(username=username, password=password, server=server, databaseName=databaseName)

    # Create the engine
    if DatabaseType == 'MSSQL':
        d.engine = create_engine(connectionString, use_setinputsizes=False, echo=False)
    else:
        d.engine = create_engine(connectionString, echo=False)

    # Check if the database exists
    if not database_exists(d.engine.url):
        logging.critical('Database %s does not exist', databaseName)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Connect to the database
    try:
        conn = d.engine.connect()
    except OperationalError:
        logging.critical('Connection error for database %s', databaseName)
        logging.shutdown()
        sys.exit(d.EX_UNAVAILABLE)
    except Exception as e:
        logging.critical('Connection error for database %s:%s', databaseName, e.args)
        logging.shutdown()
        sys.exit(d.EX_UNAVAILABLE)
    conn.close()

    # Now get the metadata and build a session maker
    d.metadata = MetaData()
    d.metadata.reflect(bind=d.engine)
    d.Session = sessionmaker(bind=d.engine)
    return


def checkWorksheet(wb, sheet, table, toBeAdded):
    '''
    Check that a worksheet exist in the workbook and that the name of the sheet matches a database table,
    and that the sheet has column headings that match the database table column names,
    and that the data in this sheet matches the defined datatype for the columns in the table.
    '''
    # Check that this worksheet exits
    if sheet not in wb.sheetnames:
        logging.critical('No sheet name "%s" in workbook', sheet)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if table not in d.metadata.tables:
        logging.critical('Missing database table "%s"', table)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Check this worksheet
    ws = wb[sheet]

    # Make sure every column in the this worksheet matches a column name in this table
    # and that every cell has data of the correct data type
    found = []
    for col in ws.columns:
        heading = True
        for cell in col:
            if heading:
                if not isinstance(cell.value, str):
                    logging.critical('Invalid heading "%s" (not string) in worksheet "%s" at "%s"', cell.value, sheet, cell.coordinate)
                    logging.shutdown()
                    sys.exit(d.EX_CONFIG)
                colName = cell.value
                if colName in d.metadata.tables[table].columns:
                    found.append(colName)
                else:
                    logging.critical('Extraneous column "%s" in worksheet "%s" at "%s"', colName, sheet, cell.coordinate)
                    logging.shutdown()
                    sys.exit(d.EX_CONFIG)
                colType = d.metadata.tables[table].columns[colName].type.python_type
                heading = False
                continue
            if cell.value is None:
                break
            if not isinstance(cell.value, colType):
                failed = True
                if isinstance(cell.value, int) and ((colType == float) or (colType == decimal.Decimal)):
                    failed = False
                elif isinstance(cell.value, float):
                    if (colType == decimal.Decimal):
                        failed = False
                    elif (colType == int):
                        try:
                            x = int(cell.value)
                            if x == cell.value:
                                failed = False
                        except Exception as e:
                            pass
                if failed:
                    logging.critical('Invalid data "%s" (type %s not %s) in column "%s" in worksheet "%s" at "%s"',
                                    cell.value, type(cell.value), colType, colName, sheet, cell.coordinate)
                    logging.shutdown()
                    sys.exit(d.EX_CONFIG)

    # Check that every column in the database table has a column in the worksheet
    for col in d.metadata.tables[table].columns:
        column = col.name
        if column in toBeAdded:
            continue
        if column not in found:
            logging.critical('Database column (%s) in table "%s" not found in sheet "%s" headers', column, table, sheet)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # Check any codes that need to be in a code table
    data = ws.values
    cols = next(data)
    table_df = pd.DataFrame(list(data), columns=cols)
    for foreign_key in d.metadata.tables[table].foreign_key_constraints:
        codeColumn = foreign_key.column_keys[-1]
        if codeColumn in toBeAdded:
            continue
        # Get all the referred to codesets
        refered_table = foreign_key.referred_table
        if refered_table not in d.codeTables:     # A new codeset, add it to the dictionary of codesets
            selectText = f'SELECT {foreign_key.elements[-1].target_fullname} FROM {foreign_key.referred_table}'
            where = ''
            for column_key in foreign_key.column_keys:
                if column_key == 'hospital_code':
                    if where != '':
                        where += ' AND '
                    where += f'hospital_code = "{d.hospital_code}"'
                if column_key == 'run_code':
                    if where != '':
                        where += ' AND '
                    where += f'run_code = "{d.run_code}"'
                if column_key == 'model_code':
                    if where != '':
                        where += ' AND '
                    where += f'model_code = "{d.model_code}"'
            if where != '':
                selectText += ' WHERE ' + where
            selected = pd.read_sql_query(text(selectText), d.engine.connect())
            codes = selected.values.tolist()      # convert rows/columns to a list of lists (will be [[code]] )
            d.codeTables[refered_table] = set()
            for codeRow in codes:
                d.codeTables[refered_table].add(codeRow[0])
        # Check every foreign key value to make sure that it is in the matching codeset
        for code in table_df[codeColumn]:
            if code not in d.codeTables[refered_table]:
                logging.critical('Code "%s" in worksheet "%s" is not in database code table "%s"', code, sheet, refered_table)
                logging.critical('table codes(%s)', d.codeTables[refered_table])
                logging.shutdown()
                sys.exit(d.EX_DATAERR)
    return table_df

def addTableData(dfTable, thisTable):
    '''
    Add data from a dataframe to a database table
    '''

    # Process each row of the spreadsheet, doing an update or an append
    # [Deletes are not supported as they could break the referrential integrety of exising data]
    # Collect all the indexed columns - assume that there are foreign keys associated with these
    indexedColumns = []
    for index in d.metadata.tables[thisTable].indexes:
        for col in index.columns:
            if col.name in indexedColumns:
                continue
            indexedColumns.append(col.name)
    # Process each row
    for row in dfTable.itertuples(index=False):
        where = ''
        results = []
        # Build a where clause, based on the values of the primary key and indexed columns
        foundCols = set()
        for col in indexedColumns:
            foundCols.add(col)
            if where != '':
                where += ' AND '
            where += col + ' = "' + getattr(row, col) + '"'
        for col in d.metadata.tables[thisTable].primary_key.columns:
            colName = col.name
            if colName in indexedColumns:
                continue
            if colName in foundCols:
                continue
            foundCols.add(colName)
            if where != '':
                where += ' AND '
            value = getattr(row, colName)
            if isinstance(value, int) or isinstance(value, float):
                where += colName + ' = ' + str(value)
            elif isinstance(value, str):
                where += colName + ' = "' + value.replace('"', '\\"') + '"'
            else:
                where += colName + ' = "' + str(value).replace('"', '\\"') + '"'
        with d.Session() as session:
            results = session.scalars(select(d.metadata.tables[thisTable]).where(text(where))).all()
        logging.debug("table(%s), where(%s), results(%s)", thisTable, where, results)

        # Assemble the parameters (values to be updated, or inserted)
        params = {}
        for col in d.metadata.tables[thisTable].columns:
            colName = col.name
            if (len(results) > 0) and (colName in indexedColumns):
                continue
            param = getattr(row, colName)
            if type(param) not in [int, float, str, decimal.Decimal]:
                if param is None:
                    param = ''
                else:
                    param = str(param)
            params[colName] = param
        with d.Session() as session:
            if (len(results) > 0):      # A row exists
                if (len(params) > 0):       # Which has updatable columns (not part of primary key or foreign key)
                    logging.debug('Existing row update: updating table %s, with values %s, where %s', thisTable, params, where)
                    session.execute(update(d.metadata.tables[thisTable]).values(params).where(text(where)))
                    session.commit()
            else:
                logging.debug('New row: inserting into table %s value %s', thisTable, params)
                session.execute(insert(d.metadata.tables[thisTable]).values(params))
                session.commit()
    return

def moveCosts(fromDeptCode, fromCostType, toAmount, toDeptCode, toCostType, mappingCode, dfCosts):
    '''
    Move a cost from one account to another
    '''
    dfFromCost = dfCosts[(dfCosts['department_code'] == fromDeptCode) & (dfCosts['cost_type_code'] == fromCostType)]
    dfToCost = dfCosts[(dfCosts['department_code'] == toDeptCode) & (dfCosts['cost_type_code'] == toCostType)]
    if len(dfFromCost.index) > 0:       # Has to be something to move
        oldFromAmount = dfFromCost['cost'].iloc[0]
        if mappingCode == 'F':        # This is a fractional cost (thisAmount is actually a fraction, not a cost)
            toAmount = oldFromAmount * toAmount

        #Check to see if this  requires a new thisRow
        if len(dfToCost.index) == 0:
            newRow = {'hospital_code': d.hospital_code, 'run_code': d.run_code, 'model_code': d.model_code, 'department_code': toDeptCode, 'cost_type_code': toCostType, 'cost': toAmount}
            dfCosts = pd.concat([dfCosts, pd.DataFrame(newRow, index=[0])], ignore_index=True)
        else:
            dfCosts.loc[(dfCosts.department_code == toDeptCode) & (dfCosts.cost_type_code == toCostType), 'cost'] += toAmount
        dfCosts.loc[(dfCosts.department_code == fromDeptCode) & (dfCosts.cost_type_code == fromCostType), 'cost'] -= toAmount
    return dfCosts

def generalLedgerAdjustOrMap(adjustMap_df, costs_df, preservedCostTypes):
    '''
    Execute any adjustments or mappings
    '''
    for thisRow in adjustMap_df.itertuples(index=False):
        thisFromDeptCode = thisRow.from_department_code
        thisFromCostType = thisRow.from_cost_type_code
        thisMappingCode = thisRow.mapping_type_code
        thisAmount = thisRow.amount
        thisToDeptCode = thisRow.to_department_code
        thisToCostType = thisRow.to_cost_type_code
        preservedCostTypes.add(thisToCostType)
        costs_df = moveCosts(thisFromDeptCode, thisFromCostType, thisAmount, thisToDeptCode, thisToCostType, thisMappingCode, costs_df)
    return costs_df, preservedCostTypes
