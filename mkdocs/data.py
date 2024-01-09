'''
The common data for the Clinical Costing system.
'''

# pylint: disable=invalid-name, line-too-long


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


codeTables = {}     # A dictionary of all the codesets. key=table name, value=set(of codes)
engine = None       # The database engine
metadata = None     # The database metadata
Session = None      # The database session maker
hospital_code = None    # The code for this hospital
model_code = None       # The code for this clinical costing model
run_code = None         # The code for this clinical costing run
