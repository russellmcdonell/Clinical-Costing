#!/usr/bin/env python

# pylint: disable=unspecified-encoding, broad-exception-caught, line-too-long, invalid-name, pointless-string-statement

'''
Script createSQLAlchemyDBviews.py

A python script to create views on the Clinical Costing database tables using SQLAlchemy

    SYNOPSIS

    $ python createSQLAlchemyDBviews.py 
             [-D databaseType|--databaseType=databaseType]
             [-C configDir|--configDir=configDir]
             [-c configFile|--configFile=configFile]
             [-s Server|--Server=Server]
             [-d databaseName|--databaseName=databaseName]
             [-v loggingLevel|--verbose=logingLevel]
             [-L logDir|--logDir=logDir]
             [-l logfile|--logfile=logfile]

    REQUIRED
    -D databaseType|--databaseType=databaseType
    The type of database [eg:MSSQL/MySQL]


    OPTIONS
    -C configDir|--configDir=configDir
    The directory containing the database connection configuration file
    (default='databaseConfig')

    -c configFile|--configFile=configFile
    The database connection configuration file (default=clinical_costing.json)
    which has the default database values for each Database Type.
    These can be overwritten using command line options.

    -u userName|--userName=userName]
    The user name require to access the database

    -p password|--password=password]
    The password require to access the database

    -s server|--server=server]
    The address of the database server

    -d databaseName|--databaseName=databaseName]
    The name of the database

    -v loggingLevel|--verbose=loggingLevel
    Set the level of logging that you want (defaut INFO).

    -L logDir
    The directory where the log file will be written (default='.')

    -l logfile|--logfile=logfile
    The name of a logging file where you want all messages captured
    (default=None)

    THE MAIN CODE
    Create the views in a database, based upon the Clinical Costing schema
'''

# Import all the modules that make life easy
import sys
import os
import argparse
import logging
import collections
import json
from sqlalchemy import create_engine, MetaData, select, inspect, event, and_
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table
from sqlalchemy_utils import database_exists
import defineSQLAlchemyDB as dbConfig

# This next section is plagurised from /usr/include/sysexits.h
EX_OK = 0        # successful termination
EX_WARN = 1        # non-fatal termination with warnings

EX_USAGE = 64        # command line usage error
EX_DATAERR = 65        # data format error
EX_NOINPUT = 66        # cannot open input
EX_NOUSER = 67        # addressee unknown
EX_NOHOST = 68        # host name unknown
EX_UNAVAILABLE = 69    # service unavailable
EX_SOFTWARE = 70    # internal software error
EX_OSERR = 71        # system error (e.g., can't fork)
EX_OSFILE = 72        # critical OS file missing
EX_CANTCREAT = 73    # can't create (user) output file
EX_IOERR = 74        # input/output error
EX_TEMPFAIL = 75    # temp failure; user is invited to retry
EX_PROTOCOL = 76    # remote error in protocol
EX_NOPERM = 77        # permission denied
EX_CONFIG = 78        # configuration error


class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiler.compiles(CreateView)
def _create_view(element, compiler, **kw):
    return "CREATE VIEW %s AS %s" % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


@compiler.compiles(DropView)
def _drop_view(element, compiler, **kw):
    return "DROP VIEW %s" % (element.name)


def view_exists(ddl, target, connection, **kw):
    return ddl.name in inspect(connection).get_view_names()


def view_doesnt_exist(ddl, target, connection, **kw):
    return not view_exists(ddl, target, connection, **kw)


def view(name, metadata, selectable):
    t = table(name)

    t._columns._populate_separate_keys(
        col._make_proxy(t) for col in selectable.selected_columns
    )

    event.listen(
        metadata,
        "after_create",
        CreateView(name, selectable).execute_if(callable_=view_doesnt_exist),
    )
    event.listen(
        metadata, "before_drop", DropView(name).execute_if(callable_=view_exists)
    )
    return t



# The main code
if __name__ == '__main__':
    '''
    Create the tables in a database, that matches the Clinical Costing schema
    '''

    # Get the script name (without the '.py' extension)
    progName = os.path.basename(sys.argv[0])
    progName = progName[0:-3]        # Strip off the .py ending

    # Define the command line options
    parser = argparse.ArgumentParser(prog=progName)
    parser.add_argument('-D', '--databaseType', dest='databaseType', required=True, help='The database Type [e.g.: MSSQL/MySQL]')
    parser.add_argument('-C', '--configDir', dest='configDir', default='../databaseConfig',
                        help='The name of the directory containing the database connection configuration file (default=config)')
    parser.add_argument('-c', '--configFile', dest='configFile', default='clinical_costing.json',
                        help='The name of the configuration file (default clinical_costing.json)')
    parser.add_argument('-u', '--username', dest='username', help='The user required to access the database')
    parser.add_argument('-p', '--password', dest='password', help='The user password required to access the database')
    parser.add_argument('-s', '--server', dest='server', help='The address of the database server')
    parser.add_argument('-d', '--databaseName', dest='databaseName', help='The name of the database')
    parser.add_argument('-v', '--verbose', dest='verbose', type=int, choices=list(range(0, 5)),
                        help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument('-L', '--logDir', dest='logDir', default='.', help='The name of a logging directory')
    parser.add_argument('-l', '--logFile', dest='logFile', default=None, help='The name of the logging file')
    parser.add_argument('args', nargs=argparse.REMAINDER)

    # Parse the command line options
    args = parser.parse_args()
    configDir = args.configDir
    configFile = args.configFile
    databaseType = args.databaseType
    username = args.username
    password = args.password
    server = args.server
    databaseName = args.databaseName
    logDir = args.logDir
    logFile = args.logFile
    loggingLevel = args.verbose

    # Set up logging
    logging_levels = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARNING, 3:logging.INFO, 4:logging.DEBUG}
    logfmt = progName + ' [%(asctime)s]: %(message)s'
    if loggingLevel and (loggingLevel not in logging_levels) :
        sys.stderr.write(f'Error - invalid logging verbosity ({loggingLevel})\n')
        parser.print_usage(sys.stderr)
        sys.stderr.flush()
        sys.exit(EX_USAGE)
    if logFile :        # If sending to a file then check if the log directory exists
        # Check that the logDir exists
        if not os.path.isdir(logDir) :
            sys.stderr.write('Error - logDir ({logDir}) does not exits\n')
            parser.print_usage(sys.stderr)
            sys.stderr.flush()
            sys.exit(EX_USAGE)
        with open(os.path.join(logDir,logFile), 'w') as logfile :
            pass
        if loggingLevel :
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel], filename=os.path.join(logDir, logFile))
        else :
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', filename=os.path.join(logDir, logFile))
        print('Now logging to {os.path.join(logDir, logFile)}')
        sys.stdout.flush()
    else :
        if loggingLevel :
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
        else :
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')
        print('Now logging to sys.stderr')
        sys.stdout.flush()

    # Read in the configuration file - which must exist if required
    config = {}                 # The configuration data
    try:
        with open(os.path.join(configDir, configFile), 'rt', newline='', encoding='utf-8') as configSource:
            config = json.load(configSource, object_pairs_hook=collections.OrderedDict)
    except IOError:
        logging.critical('configFile (clincial_costing.json) failed to load')
        logging.shutdown()
        sys.exit(EX_CONFIG)

    # Check that we have a databaseName if we have a databaseType
    if databaseType not in config:
        logging.critical('databaseType(%s) not found in configuraton file(SQLAlchemyDB.json)', databaseType)
        logging.shutdown()
        sys.exit(EX_CONFIG)
    if 'connectionString' not in config[databaseType]:
        logging.critical('No %s connectionString defined in configuration file(SQLAlchemyDB.json)', databaseType)
        logging.shutdown()
        sys.exit(EX_CONFIG)
    connectionString = config[databaseType]['connectionString']
    if ('username' in config[databaseType]) and (username is None):
        username = config[databaseType]['username']
    if ('password' in config[databaseType]) and (password is None):
        password = config[databaseType]['password']
    if ('server' in config[databaseType]) and (server is None):
        server = config[databaseType]['server']
    if ('databaseName' in config[databaseType]) and (databaseName is None):
        databaseName = config[databaseType]['databaseName']

    # Check that we have all the required paramaters
    if username is None:
        logging.critical('Missing definition for "username"')
        logging.shutdown()
        sys.exit(EX_USAGE)
    if password is None:
        logging.critical('Missing definition for "password"')
        logging.shutdown()
        sys.exit(EX_USAGE)
    if server is None:
        logging.critical('Missing definition for "server"')
        logging.shutdown()
        sys.exit(EX_USAGE)
    if databaseName is None:
        logging.critical('Missing definition for "databaseName"')
        logging.shutdown()
        sys.exit(EX_USAGE)
    connectionString = connectionString.format(username=username, password=password, server=server, databaseName=databaseName)

    # Create the engine
    if databaseType == 'MSSQL':
        engine = create_engine(connectionString, use_setinputsizes=False, echo=True)
    else:
        engine = create_engine(connectionString, echo=True)

    # Check if the database exists
    if not database_exists(engine.url):
        logging.critical('Database %s does not exist', databaseName)
        logging.shutdown()
        sys.exit(EX_CONFIG)

    # Connect to the database
    try:
        conn = engine.connect()
    except OperationalError:
        logging.critical('Connection error for database %s', databaseName)
        logging.shutdown()
        sys.exit(EX_UNAVAILABLE)
    except Exception as e:
        logging.critical('Connection error for database %s', databaseName)
        logging.shutdown()
        sys.exit(EX_UNAVAILABLE)
    conn.close()

    # Now get the metadata
    metaData = dbConfig.Base.metadata

    # Define the views
    # the .label() is to suit SQLite which needs explicit label names
    # to be given when creating the view
    # See http://www.sqlite.org/c3ref/column_name.html
    inpatDRGcots = view(
        "inpatDRGcosts",
        metaData,
        select(
            metaData.tables['inpat_episode_details'].c.drg.label("drg"),
            metaData.tables['inpat_episode_details'].c.hospital_code.label("hospital_code"),
            metaData.tables['event_costs'].c.model_code.label("model_code"),
            metaData.tables['inpat_episode_details'].c.run_code.label("run_code"),
            metaData.tables['event_costs'].c.event_code.label("event_code"),
            metaData.tables['event_costs'].c.event_attribute_code.label("event_attribute_code"),
            metaData.tables['event_costs'].c.service_code.label("service_code"),
            metaData.tables['inpat_episode_details'].c.episode_no.label("episode_no"),
            metaData.tables['event_costs'].c.event_seq.label("event_seq"),
            metaData.tables['event_costs'].c.department_code.label("department_code"),
            metaData.tables['event_costs'].c.cost_type_code.label("cost_type_code"),
            metaData.tables['event_costs'].c.event_what.label("event_what"),
            metaData.tables['event_costs'].c.distribution_code.label("distribution_code"),
            metaData.tables['event_costs'].c.cost.label("cost"),
        )
        .select_from(metaData.tables['inpat_episode_details'].join(metaData.tables['event_costs'], and_(metaData.tables['inpat_episode_details'].c.hospital_code == metaData.tables['event_costs'].c.hospital_code,
                                                                  metaData.tables['inpat_episode_details'].c.run_code == metaData.tables['event_costs'].c.run_code,
                                                                  metaData.tables['inpat_episode_details'].c.episode_no == metaData.tables['event_costs'].c.episode_no)))
        .where(metaData.tables['event_costs'].c.service_code == "Inpat"),
    )

    inpatClinicalSpecialtyCosts = view(
        "inpatClinicalSpecialtyCosts",
        metaData,
        select(
            metaData.tables['inpat_episode_details'].c.clinical_specialty.label("clinical_specialty"),
            metaData.tables['inpat_episode_details'].c.hospital_code.label("hospital_code"),
            metaData.tables['event_costs'].c.model_code.label("model_code"),
            metaData.tables['inpat_episode_details'].c.run_code.label("run_code"),
            metaData.tables['event_costs'].c.event_code.label("event_code"),
            metaData.tables['event_costs'].c.event_attribute_code.label("event_attribute_code"),
            metaData.tables['event_costs'].c.service_code.label("service_code"),
            metaData.tables['inpat_episode_details'].c.episode_no.label("episode_no"),
            metaData.tables['event_costs'].c.event_seq.label("event_seq"),
            metaData.tables['event_costs'].c.department_code.label("department_code"),
            metaData.tables['event_costs'].c.cost_type_code.label("cost_type_code"),
            metaData.tables['event_costs'].c.event_what.label("event_what"),
            metaData.tables['event_costs'].c.distribution_code.label("distribution_code"),
            metaData.tables['event_costs'].c.cost.label("cost"),
        )
        .select_from(metaData.tables['inpat_episode_details'].join(metaData.tables['event_costs'], and_(metaData.tables['inpat_episode_details'].c.hospital_code == metaData.tables['event_costs'].c.hospital_code,
                                                                  metaData.tables['inpat_episode_details'].c.run_code == metaData.tables['event_costs'].c.run_code,
                                                                  metaData.tables['inpat_episode_details'].c.episode_no == metaData.tables['event_costs'].c.episode_no)))
        .where(metaData.tables['event_costs'].c.service_code == "Inpat"),
    )

    # Create all the views
    try:
        with engine.begin() as conn:
            metaData.create_all(conn)
    except Exception as e:
        print('Exception:', e)
        logging.shutdown()
        sys.exit(EX_UNAVAILABLE)

    print('All views have been created')
    logging.shutdown()
    sys.exit(EX_OK)
