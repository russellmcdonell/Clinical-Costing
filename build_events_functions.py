'''
The common Event building functions for the Clinical Costing system.
'''

# pylint: disable=invalid-name, line-too-long, broad-exception-caught, unused-variable, not-callable, unused-argument

import sys
import logging
import inspect
import pandas as pd
from sqlalchemy import text, insert
import data as d

SQLwhere = None
SQLwhereRun = None
SQLwhereModel = None
SQLwhereHospital = None

def buildEvent(eventFunc, eventCode, eventAttribute, eventWhat, eventWhere, eventBase, eventWeight, eventAcuityScaling):
    '''
    Build an Event using the function "eventFunc"
    '''
    if (eventFunc not in globals()) or not inspect.isfunction(globals()[eventFunc]):
        logging.critical('Event function "%s" is not defined', eventFunc)
        logging.shutdown()
        sys.exit(d.EX_USAGE)
    globals()[eventFunc](eventCode, eventAttribute, eventWhat, eventWhere, eventBase, eventWeight, eventAcuityScaling)

def baseParams(code, attribute, what):
    '''
    Build the base parameters
    '''
    params = {}
    params['hospital_code'] = d.hospital_code
    params['run_code'] = d.run_code
    params['model_code'] = d.model_code
    params['event_code'] = code
    params['event_attribute_code'] = attribute
    params['service_code'] = 'Inpat'
    params['episode_no'] = 1
    params['event_seq'] = 1
    params['event_what'] = what
    params['distribution_code'] = code
    params['event_weight'] = 1.0
    return params

def checkDistributionCode(distributionCode, eventCode, eventAttribute, unit):
    '''
    Check a distribution_code and, if necessary, create a new one
    '''
    if distributionCode in d.codeTables['distribution_codes']:
        return
    distributionDescription = d.codeTables['event_codes'][eventCode] + ', ' + d.codeTables['event_attribute_codes'][eventAttribute]
    if unit is not None:
        if unit in d.codeTables['ward_codes']:
            distributionDescription += f" for ward ({unit}) - {d.codeTables['ward_codes'][unit]}"
        elif unit in d.codeTables['clinic_codes']:
            distributionDescription += f" for clinic ({unit}) - {d.codeTables['clinic_codes'][unit]}"
    params = {}
    params['hospital_code'] = d.hospital_code
    params['model_code'] = d.model_code
    params['distribution_code'] = distributionCode
    params['distribution_description'] = distributionDescription
    with d.Session() as session:
        session.execute(insert(d.metadata.tables['distribution_codes']).values(params))
        session.commit()
    d.codeTables['distribution_codes'][distributionCode] = distributionDescription
    return

def adjustAcuity(thisAcuity, acuityScaling):
    '''
    Adjust acuity, based upon acuity scaling
    '''
    if acuityScaling >= 1.0:        # Increase the acuity
        if thisAcuity < 1.0:            # By reducing the reduction
            thisAcuity = 1.0 - (1.0 - thisAcuity) / acuityScaling
        else:                           # By increasing the increase
            thisAcuity *= acuityScaling
    elif thisAcuity < 1.0:      # Reduce the acuity by increasing the reduction
        thisAcuity = 1.0 - (1 - thisAcuity) * acuityScaling
    else:                       # Reduce the acuity by reducing the increase
        thisAcuity = 1.0 + (thisAcuity - 1.0) * acuityScaling
    return thisAcuity


def EDadmissions(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based admissions to the Accidenta and Emergency department
    '''
    if code not in d.codeTables['distribution_codes']:
        logging.critical('distribution code(%s) not in distribution_codes(%s)', code, d.codeTables['distribution_codes'])
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    params = baseParams(code, attribute, what)
    params['service_code'] = 'ED'
    selectText = 'SELECT episode_no FROM ed_admissions WHERE ' + SQLwhereRun
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in events_df.itertuples():
        params['episode_no'] = row.episode_no
        with d.Session() as session:
            session.execute(insert(d.metadata.tables['events']).values(params))
            session.commit()

def EDdischarges(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on discharges from the Accident and Emergency department
    '''
    if code not in d.codeTables['distribution_codes']:
        logging.critical('distribution code(%s) not in distribution_codes(%s)', code, d.codeTables['distribution_codes'])
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    params = baseParams(code, attribute, what)
    params['service_code'] = 'ED'
    selectText = 'SELECT episode_no FROM ed_discharges WHERE ' + SQLwhereRun
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in events_df.itertuples():
        params['episode_no'] = row.episode_no
        with d.Session() as session:
            session.execute(insert(d.metadata.tables['events']).values(params))
            session.commit()

def EDattendmin(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on minutes in the Accident and Emergency department
    '''
    if code not in d.codeTables['distribution_codes']:
        logging.critical('distribution code(%s) not in distribution_codes(%s)', code, d.codeTables['distribution_codes'])
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    params = baseParams(code, attribute, what)
    params['service_code'] = 'ED'
    selectText = 'SELECT episode_no, attend_min, acuity FROM ed_episode_details WHERE ' + SQLwhereRun
    if (where is not None) and (where != ''):
        selectText += ' AND ' + where
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in events_df.itertuples():
        params['episode_no'] = row.episode_no
        thisAcuity = adjustAcuity(row.acuity, acuityScaling)
        thisWeight = (base + row.attend_min * thisAcuity) * weight
        params['event_weight'] = thisWeight
        with d.Session() as session:
            session.execute(insert(d.metadata.tables['events']).values(params))
            session.commit()

def EDseenmin(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on minutes seen by a nurse the Accident and Emergency department
    '''
    if code not in d.codeTables['distribution_codes']:
        logging.critical('distribution code(%s) not in distribution_codes(%s)', code, d.codeTables['distribution_codes'])
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    params = baseParams(code, attribute, what)
    params['service_code'] = 'ED'
    selectText = 'SELECT episode_no, seen_min, acuity FROM ed_episode_details WHERE ' + SQLwhereRun
    if (where is not None) and (where != ''):
        selectText += ' AND ' + where
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in events_df.itertuples():
        params['episode_no'] = row.episode_no
        thisAcuity = adjustAcuity(row.acuity, acuityScaling)
        thisWeight = (base + row.seen_min * thisAcuity) * weight
        params['event_weight'] = thisWeight
        with d.Session() as session:
            session.execute(insert(d.metadata.tables['events']).values(params))
            session.commit()

def EDtreatmin(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on minutes of treatment in the Accident and Emergency department
    '''
    if code not in d.codeTables['distribution_codes']:
        logging.critical('distribution code(%s) not in distribution_codes(%s)', code, d.codeTables['distribution_codes'])
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    params = baseParams(code, attribute, what)
    params['service_code'] = 'ED'
    selectText = 'SELECT episode_no, treat_min, acuity FROM ed_episode_details WHERE ' + SQLwhereRun
    if (where is not None) and (where != ''):
        selectText += ' AND ' + where
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in events_df.itertuples():
        params['episode_no'] = row.episode_no
        thisAcuity = adjustAcuity(row.acuity, acuityScaling)
        thisWeight = (base + row.treat_min * thisAcuity) * weight
        params['event_weight'] = thisWeight
        with d.Session() as session:
            session.execute(insert(d.metadata.tables['events']).values(params))
            session.commit()

def opclinicmin(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on minutes in an outpatient clinic
    '''
    params = baseParams(code, attribute, what)
    params['service_code'] = 'Clinic'
    if code.startswith('clinic'):
        selectText = 'SELECT episode_no, attend_min, clinic_code, acuity FROM clinic_activity_details WHERE ' + SQLwhereRun
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            clinicCode = row.clinic_code
            distributionCode = clinicCode + code[6:]
            params['distribution_code'] = distributionCode
            if distributionCode not in d.codeTables['distribution_codes']:
                logging.critical('distribution code(%s) not in distribution_codes(%s)', distributionCode, d.codeTables['distribution_codes'])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            thisAcuity = adjustAcuity(row.acuity, acuityScaling)
            thisWeight = (base + row.attend_min * thisAcuity) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()
    else:
        selectText = 'SELECT episode_no, sum(attend_min * acuity) as eventWeight FROM clinic_activity_details WHERE ' + SQLwhereRun
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        selectText += ' GROUP BY episode_no'
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            distributionCode = code
            params['distribution_code'] = distributionCode
            if distributionCode not in d.codeTables['distribution_codes']:
                logging.critical('distribution code(%s) not in distribution_codes(%s)', distributionCode, d.codeTables['distribution_codes'])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            thisWeight = (base + row.eventWeight) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()

def ipadmissions(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on admissions to an inpatient ward
    '''
    params = baseParams(code, attribute, what)
    if code.startswith('ward'):
        selectText = 'SELECT inpat_episode_details.episode_no as episode_no, inpat_episode_details.admitting_ward_code as ward_code,'
        selectText += ' inpat_episode_details.acuity as acuity'
        selectText += ' FROM inpat_episode_details, inpat_admissions WHERE'
        selectText += f' inpat_episode_details.hospital_code = "{d.hospital_code}" AND inpat_admissions.hospital_code = "{d.hospital_code}"'
        selectText += f' AND inpat_episode_details.run_code = "{d.run_code}" AND inpat_admissions.run_code = "{d.run_code}"'
        selectText += ' AND inpat_episode_details.episode_no =  inpat_admissions.episode_no'
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            wardCode = row.ward_code
            distributionCode = wardCode + code[4:]
            checkDistributionCode(distributionCode, code, attribute, wardCode)
            params['distribution_code'] = distributionCode
            thisAcuity = adjustAcuity(row.acuity, acuityScaling)
            thisWeight = (base + thisAcuity) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()
    else:
        selectText = 'SELECT inpat_episode_details.episode_no as episode_no, inpat_episode_details.acuity as acuity'
        selectText += ' FROM inpat_episode_details, inpat_admissions WHERE'
        selectText += f' inpat_episode_details.hospital_code = "{d.hospital_code}" AND inpat_admissions.hospital_code = "{d.hospital_code}"'
        selectText += f' AND inpat_episode_details.run_code = "{d.run_code}" AND inpat_admissions.run_code = "{d.run_code}"'
        selectText += ' AND inpat_episode_details.episode_no =  inpat_admissions.episode_no'
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            distributionCode = code
            if distributionCode not in d.codeTables['distribution_codes']:
                logging.critical('distribution code(%s) not in distribution_codes(%s)', distributionCode, d.codeTables['distribution_codes'])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            params['distribution_code'] = distributionCode
            thisAcuity = adjustAcuity(row.acuity, acuityScaling)
            thisWeight = (base + thisAcuity) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()

def ipdischarges(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on inpatient discharges
    '''
    params = baseParams(code, attribute, what)
    if code.startswith('ward'):
        selectText = 'SELECT inpat_episode_details.episode_no as episode_no, inpat_episode_details.discharge_ward_code as ward_code,'
        selectText += ' inpat_episode_details.acuity as acuity'
        selectText += ' FROM inpat_episode_details, inpat_discharges WHERE'
        selectText += f' inpat_episode_details.hospital_code = "{d.hospital_code}" AND inpat_discharges.hospital_code = "{d.hospital_code}"'
        selectText += f' AND inpat_episode_details.run_code = "{d.run_code}" AND inpat_discharges.run_code = "{d.run_code}"'
        selectText += ' AND inpat_episode_details.episode_no =  inpat_discharges.episode_no'
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            wardCode = row.ward_code
            distributionCode = wardCode + code[4:]
            checkDistributionCode(distributionCode, code, attribute, wardCode)
            params['distribution_code'] = distributionCode
            thisAcuity = adjustAcuity(row.acuity, acuityScaling)
            thisWeight = (base + thisAcuity) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()
    else:
        selectText = 'SELECT inpat_episode_details.episode_no as episode_no, inpat_episode_details.acuity as acuity'
        selectText += ' FROM inpat_episode_details, inpat_discharges WHERE'
        selectText += f' inpat_episode_details.hospital_code = "{d.hospital_code}" AND inpat_discharges.hospital_code = "{d.hospital_code}"'
        selectText += f' AND inpat_episode_details.run_code = "{d.run_code}" AND inpat_discharges.run_code = "{d.run_code}"'
        selectText += ' AND inpat_episode_details.episode_no =  inpat_discharges.episode_no'
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            distributionCode = code
            if distributionCode not in d.codeTables['distribution_codes']:
                logging.critical('distribution code(%s) not in distribution_codes(%s)', distributionCode, d.codeTables['distribution_codes'])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            params['distribution_code'] = distributionCode
            thisAcuity = adjustAcuity(row.acuity, acuityScaling)
            thisWeight = (base + thisAcuity) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()

def ipwardbdays(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on days in an inpatient ward
    '''
    params = baseParams(code, attribute, what)
    if code.startswith('ward'):
        selectText = 'SELECT inpat_episode_details.episode_no as episode_no, inpat_patient_location.location_seq as event_seq, inpat_patient_location.ward_code as ward_code,'
        selectText += ' inpat_patient_location.ward_days as ward_days, inpat_patient_location.acuity as acuity'
        selectText += ' FROM inpat_episode_details, inpat_patient_location WHERE'
        selectText += f' inpat_episode_details.hospital_code = "{d.hospital_code}" AND inpat_patient_location.hospital_code = "{d.hospital_code}"'
        selectText += f' AND inpat_episode_details.run_code = "{d.run_code}" AND inpat_patient_location.run_code = "{d.run_code}"'
        selectText += ' AND inpat_episode_details.episode_no =  inpat_patient_location.episode_no'
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            params['event_seq'] = row.event_seq
            wardCode = row.ward_code
            distributionCode = wardCode + code[4:]
            checkDistributionCode(distributionCode, code, attribute, wardCode)
            params['distribution_code'] = distributionCode
            thisAcuity = adjustAcuity(row.acuity, acuityScaling)
            thisWeight = (base + row.ward_days * thisAcuity) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()
    else:
        selectText = 'SELECT inpat_episode_details.episode_no as episode_no,'
        selectText += ' sum(inpat_patient_location.ward_days * inpat_patient_location.acuity) as eventWeight'
        selectText += ' FROM inpat_episode_details, inpat_patient_location WHERE'
        selectText += f' inpat_episode_details.hospital_code = "{d.hospital_code}" AND inpat_patient_location.hospital_code = "{d.hospital_code}"'
        selectText += f' AND inpat_episode_details.run_code = "{d.run_code}" AND inpat_patient_location.run_code = "{d.run_code}"'
        selectText += ' AND inpat_episode_details.episode_no =  inpat_patient_location.episode_no'
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        selectText += ' GROUP BY inpat_episode_details.episode_no'
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            distributionCode = code
            if distributionCode not in d.codeTables['distribution_codes']:
                logging.critical('distribution code(%s) not in distribution_codes(%s)', distributionCode, d.codeTables['distribution_codes'])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            params['distribution_code'] = distributionCode
            thisWeight = (base + row.eventWeight) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()


def ipwardsday(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on a same day attendance in an inpatient ward
    '''
    params = baseParams(code, attribute, what)
    selectText = 'SELECT episode_no, admitting_ward_code, acuity FROM inpat_episode_details WHERE ' + SQLwhereRun
    selectText += ' AND same_day = 1'
    if (where is not None) and (where != ''):
        selectText += ' AND ' + where
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in events_df.itertuples():
        params['episode_no'] = row.episode_no
        wardCode = row.admitting_ward_code
        if code.startswith('ward'):
            distributionCode = wardCode + code[4:]
            checkDistributionCode(distributionCode, code, attribute, wardCode)
        else:
            distributionCode = code
            if distributionCode not in d.codeTables['distribution_codes']:
                logging.critical('distribution code(%s) not in distribution_codes(%s)', distributionCode, d.codeTables['distribution_codes'])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
        params['distribution_code'] = distributionCode
        thisAcuity = adjustAcuity(row.acuity, acuityScaling)
        thisWeight = (base + thisAcuity) * weight
        params['event_weight'] = thisWeight
        with d.Session() as session:
            session.execute(insert(d.metadata.tables['events']).values(params))
            session.commit()

def ipwardbhrs(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based hours in an inpatient ward
    '''
    params = baseParams(code, attribute, what)
    if code.startswith('ward'):
        selectText = 'SELECT inpat_episode_details.episode_no as episode_no, inpat_patient_location.location_seq as event_seq, inpat_patient_location.ward_code as ward_code,'
        selectText += ' inpat_patient_location.ward_hours as ward_hours, inpat_patient_location.acuity as acuity'
        selectText += ' FROM inpat_episode_details, inpat_patient_location WHERE'
        selectText += f' inpat_episode_details.hospital_code = "{d.hospital_code}" AND inpat_patient_location.hospital_code = "{d.hospital_code}"'
        selectText += f' AND inpat_episode_details.run_code = "{d.run_code}" AND inpat_patient_location.run_code = "{d.run_code}"'
        selectText += ' AND inpat_episode_details.episode_no =  inpat_patient_location.episode_no'
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            params['event_seq'] = row.event_seq
            wardCode = row.ward_code
            distributionCode = wardCode + code[4:]
            checkDistributionCode(distributionCode, code, attribute, wardCode)
            params['distribution_code'] = distributionCode
            thisAcuity = adjustAcuity(row.acuity, acuityScaling)
            thisWeight = (base + row.ward_hours * thisAcuity) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()
    else:
        selectText = 'SELECT inpat_episode_details.episode_no as episode_no,'
        selectText += ' sum(inpat_patient_location.ward_hours * inpat_patient_location.acuity) as eventWeight'
        selectText += ' FROM inpat_episode_details, inpat_patient_location WHERE'
        selectText += f' inpat_episode_details.hospital_code = "{d.hospital_code}" AND inpat_patient_location.hospital_code = "{d.hospital_code}"'
        selectText += f' AND inpat_episode_details.run_code = "{d.run_code}" AND inpat_patient_location.run_code = "{d.run_code}"'
        selectText += ' AND inpat_episode_details.episode_no =  inpat_patient_location.episode_no'
        if (where is not None) and (where != ''):
            selectText += ' AND ' + where
        selectText += ' GROUP BY inpat_episode_details.episode_no'
        events_df = pd.read_sql_query(text(selectText), d.engine.connect())
        for row in events_df.itertuples():
            params['episode_no'] = row.episode_no
            distributionCode = code
            if distributionCode not in d.codeTables['distribution_codes']:
                logging.critical('distribution code(%s) not in distribution_codes(%s)', distributionCode, d.codeTables['distribution_codes'])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            params['distribution_code'] = distributionCode
            thisWeight = (base + row.eventWeight) * weight
            params['event_weight'] = thisWeight
            with d.Session() as session:
                session.execute(insert(d.metadata.tables['events']).values(params))
                session.commit()

def anaesthmin(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on minutes of anaethesia
    '''
    if code not in d.codeTables['distribution_codes']:
        logging.critical('distribution code(%s) not in distribution_codes(%s)', code, d.codeTables['distribution_codes'])
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    params = baseParams(code, attribute, what)
    selectText = 'SELECT episode_no, surgery_seq, anaesthetic_mins, theatre_acuity FROM inpat_theatre_details WHERE ' + SQLwhereRun
    if (where is not None) and (where != ''):
        selectText += ' AND ' + where
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in events_df.itertuples():
        params['episode_no'] = row.episode_no
        params['event_seq'] = row.surgery_seq
        thisWeight = (base + row.anaesthetic_mins * row.theatre_acuity) * weight
        params['event_weight'] = thisWeight
        with d.Session() as session:
            session.execute(insert(d.metadata.tables['events']).values(params))
            session.commit()

def theatremin(code, attribute, what, where, base, weight, acuityScaling):
    '''
    Build events based on minutes in an operating theatre
    '''
    if code not in d.codeTables['distribution_codes']:
        logging.critical('distribution code(%s) not in distribution_codes(%s)', code, d.codeTables['distribution_codes'])
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    params = baseParams(code, attribute, what)
    selectText = 'SELECT episode_no, surgery_seq, theatre_mins, theatre_acuity FROM inpat_theatre_details WHERE ' + SQLwhereRun
    if (where is not None) and (where != ''):
        selectText += ' AND ' + where
    events_df = pd.read_sql_query(text(selectText), d.engine.connect())
    for row in events_df.itertuples():
        params['episode_no'] = row.episode_no
        params['event_seq'] = row.surgery_seq
        thisWeight = (base + row.theatre_mins * row.theatre_acuity) * weight
        params['event_weight'] = thisWeight
        with d.Session() as session:
            session.execute(insert(d.metadata.tables['events']).values(params))
            session.commit()
