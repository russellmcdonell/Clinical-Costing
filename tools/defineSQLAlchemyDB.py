
'''
-- SQLAchemy definition of the Clinical Costing database tables
'''

# pylint: disable=unused-private-member, missing-class-docstring, line-too-long, invalid-name

import datetime
from sqlalchemy import String, Date, Integer, Float, Index, ForeignKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

# The per-hospital configuration tables
class hospitals(Base):
    '''
    The hospitals for which Clinical Costs are being calculated.
    '''
    __tablename__ = 'hospitals'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    hospital_name:Mapped[str] = mapped_column(String(50), nullable=True)

class departments(Base):
    """
    The departments in this hospital's general ledger.
    """
    __tablename__ = 'departments'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_name:Mapped[str] = mapped_column(String(50), nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'department_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
    )

class cost_types(Base):
    """
    The cost types in this hospital's general ledger.
    """
    __tablename__ = 'cost_types'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_description:Mapped[str] = mapped_column(String(50), nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'cost_type_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
    )

class services(Base):
    """
    The Services run by this hospital.
    """
    __tablename__ = 'services'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    service_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    service_description:Mapped[str] = mapped_column(String(50), primary_key=False, autoincrement=False)
    __table_args__ = (
        Index(None, 'hospital_code', 'service_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
    )

class wards(Base):
    """
    The wards in this hospital.
    """
    __tablename__ = 'wards'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    ward_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    ward_description:Mapped[str] = mapped_column(String(50), nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'ward_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
    )

class theatres(Base):
    """
    The theatres in this hospital.
    """
    __tablename__ = 'theatres'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    theatre_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    theatre_description:Mapped[str] = mapped_column(String(50), nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'theatre_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
    )

class clinics(Base):
    """
    The outpatient clinics in this hospital.
    """
    __tablename__ = 'clinics'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    clinic_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    clinic_description:Mapped[str] = mapped_column(String(50), nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'clinic_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
    )

class clinicians(Base):
    """
    The clinicians working in this hospital.
    """
    __tablename__ = 'clinicians'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    clinician_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    clinician_description:Mapped[str] = mapped_column(String(50), nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'clinician_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
    )


# Per-hospital details for each Clinical Costing run
class clinical_costing_runs(Base):
    '''
    The run code, run name, start date and end date for each Clinical Costing run
    (Can be used for more than one hospital)
    '''
    __tablename__ = 'clinical_costing_runs'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_description:Mapped[str] = mapped_column(String(50), nullable=True)
    start_date:Mapped[datetime.date] = mapped_column(Date, nullable=True)
    end_date:Mapped[datetime.date] = mapped_column(Date, nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
    )

# The per-hospital patient activity extracts tables
class Inpat_episode_details(Base):
    '''
    The facts (measures) and dimensions (codes) associated with each inpatient episode for this hospital
    that is included in this patient activity extract.
    '''
    __tablename__ = 'inpat_episode_details'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    dch_episode_no:Mapped[int] = mapped_column(Integer, nullable=True)
    acuity:Mapped[int] = mapped_column(Integer, nullable=True)
    drg:Mapped[str] = mapped_column(String(12), nullable=True)
    care_type:Mapped[str] = mapped_column(String(12), nullable=True)
    clinical_specialty:Mapped[str] = mapped_column(String(12), nullable=True)
    admitting_ward_code:Mapped[str] = mapped_column(String(12), nullable=True)
    admitting_doctor_code:Mapped[str] = mapped_column(String(12), nullable=True)
    discharge_ward_code:Mapped[str] = mapped_column(String(12), nullable=True)
    bed_days:Mapped[int] = mapped_column(Integer, nullable=True)
    bed_hours:Mapped[int] = mapped_column(Integer, nullable=True)
    prev_bdays:Mapped[int] = mapped_column(Integer, nullable=True)
    prev_bhours:Mapped[int] = mapped_column(Integer, nullable=True)
    same_day:Mapped[int] = mapped_column(Integer, nullable=True)
    transfers:Mapped[int] = mapped_column(Integer, nullable=True)
    pat_cat:Mapped[str] = mapped_column(String(12), nullable=True)
    fin_cat:Mapped[str] = mapped_column(String(12), nullable=True)
    sex:Mapped[str] = mapped_column(String(12), nullable=True)
    ethnicity:Mapped[str] = mapped_column(String(12), nullable=True)
    postcode:Mapped[str] = mapped_column(String(12), nullable=True)
    revenue:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'admitting_ward_code'], ['wards.hospital_code', 'wards.ward_code']),
        ForeignKeyConstraint(['hospital_code', 'admitting_doctor_code'], ['clinicians.hospital_code', 'clinicians.clinician_code']),
        ForeignKeyConstraint(['hospital_code', 'discharge_ward_code'], ['wards.hospital_code', 'wards.ward_code']),
    )

class Inpat_admissions(Base):
    '''
    The list of inpatient episodes for this hospital that were admitted during the extract period.
    '''
    __tablename__ = 'inpat_admissions'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code', 'episode_no'], ['inpat_episode_details.hospital_code', 'inpat_episode_details.run_code', 'inpat_episode_details.episode_no']),
    )

class Inpat_discharges(Base):
    '''
    The list of inpatient episodes for this hospital that were discharged during the extrac period.
    '''
    __tablename__ = 'inpat_discharges'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code', 'episode_no'], ['inpat_episode_details.hospital_code', 'inpat_episode_details.run_code', 'inpat_episode_details.episode_no']),
    )

class Inpat_patient_location(Base):
    '''
    The locations and location durations for each inpatient episode for this hospital
    that is included in this activity extract
    '''
    __tablename__ = 'inpat_patient_location'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    location_seq:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    ward_code:Mapped[str] = mapped_column(String(12), nullable=True)
    ward_days:Mapped[int] = mapped_column(Integer, nullable=True)
    ward_hours:Mapped[int] = mapped_column(Integer, nullable=True)
    acuity:Mapped[int] = mapped_column(Integer, nullable=True)
    revenue:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code', 'episode_no'], ['inpat_episode_details.hospital_code', 'inpat_episode_details.run_code', 'inpat_episode_details.episode_no']),
        ForeignKeyConstraint(['hospital_code', 'ward_code'], ['wards.hospital_code', 'wards.ward_code']),
    )

class Inpat_theatre_details(Base):
    '''
    The details of any theatre activity associated with each inpatient episode for this hospital
    that is included in this activity extract
    '''
    __tablename__ = 'inpat_theatre_details'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    surgery_seq:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    theatre_code:Mapped[str] = mapped_column(String(12), nullable=True)
    surgeon_code:Mapped[str] = mapped_column(String(12), nullable=True)
    anaesth_code:Mapped[str] = mapped_column(String(12), nullable=True)
    procedure:Mapped[str] = mapped_column(String(12), nullable=True)
    theatre_mins:Mapped[int] = mapped_column(Integer, nullable=True)
    surgery_mins:Mapped[int] = mapped_column(Integer, nullable=True)
    anaesthetic_mins:Mapped[int] = mapped_column(Integer, nullable=True)
    theatre_acuity:Mapped[int] = mapped_column(Integer, nullable=True)
    revenue:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code', 'episode_no'], ['inpat_episode_details.hospital_code', 'inpat_episode_details.run_code', 'inpat_episode_details.episode_no']),
        ForeignKeyConstraint(['hospital_code', 'theatre_code'], ['theatres.hospital_code', 'theatres.theatre_code']),
        ForeignKeyConstraint(['hospital_code', 'surgeon_code'], ['clinicians.hospital_code', 'clinicians.clinician_code']),
        ForeignKeyConstraint(['hospital_code', 'anaesth_code'], ['clinicians.hospital_code', 'clinicians.clinician_code']),
    )

class Clinic_activity_details(Base):
    '''
    The details of each outpatient attendance for this hospital
    that is included in this activity extract
    '''
    __tablename__ = 'clinic_activity_details'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    attend_min:Mapped[int] = mapped_column(Integer, nullable=True)
    clinic_code:Mapped[int] = mapped_column(String(12), nullable=True)
    practitioner_code:Mapped[int] = mapped_column(String(12), nullable=True)
    pat_cat:Mapped[str] = mapped_column(String(12), nullable=True)
    fin_cat:Mapped[str] = mapped_column(String(12), nullable=True)
    sex:Mapped[str] = mapped_column(String(12), nullable=True)
    ethnicity:Mapped[str] = mapped_column(String(12), nullable=True)
    postcode:Mapped[str] = mapped_column(String(12), nullable=True)
    acuity:Mapped[int] = mapped_column(Integer, nullable=True)
    revenue:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'clinic_code'], ['clinics.hospital_code', 'clinics.clinic_code']),
        ForeignKeyConstraint(['hospital_code', 'practitioner_code'], ['clinicians.hospital_code', 'clinicians.clinician_code']),
    )

class ED_episode_details(Base):
    '''
    The facts (measures) and dimensions (codes) associated with each Emergency department episode for this hospital
    that is included in this patient activity extract.
    '''
    __tablename__ = 'ed_episode_details'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    attend_min:Mapped[int] = mapped_column(Integer, nullable=True)
    seen_min:Mapped[int] = mapped_column(Integer, nullable=True)
    treat_min:Mapped[int] = mapped_column(Integer, nullable=True)
    urgency:Mapped[int] = mapped_column(Integer, nullable=True)
    doctor_code:Mapped[str] = mapped_column(String(12), nullable=True)
    adm_source:Mapped[str] = mapped_column(String(12), nullable=True)
    dch_destn:Mapped[str] = mapped_column(String(12), nullable=True)
    pat_cat:Mapped[str] = mapped_column(String(12), nullable=True)
    fin_cat:Mapped[str] = mapped_column(String(12), nullable=True)
    sex:Mapped[str] = mapped_column(String(12), nullable=True)
    ethnicity:Mapped[str] = mapped_column(String(12), nullable=True)
    postcode:Mapped[str] = mapped_column(String(12), nullable=True)
    acuity:Mapped[int] = mapped_column(Integer, nullable=True)
    revenue:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'doctor_code'], ['clinicians.hospital_code', 'clinicians.clinician_code']),
    )

class ED_admissions(Base):
    '''
    The list of Emergency department episodes for this hospital that were admitted during the extract period.
    '''
    __tablename__ = 'ed_admissions'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code', 'episode_no'], ['ed_episode_details.hospital_code', 'ed_episode_details.run_code', 'ed_episode_details.episode_no']),
    )

class ED_discharges(Base):
    '''
    The list of Emergency department episodes for this hospital that were discharged during the extrac period.
    '''
    __tablename__ = 'ed_discharges'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    episode_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code', 'episode_no'], ['ed_episode_details.hospital_code', 'ed_episode_details.run_code', 'ed_episode_details.episode_no']),
    )

# The Events configuration tables for this hospital
class events(Base):
    __tablename__ = 'events'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    service_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    __table_args__ = (
        Index(None, 'hospital_code', 'service_code', 'event_code', unique=True),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'service_code'], ['services.hospital_code', 'services.service_code']),
    )

# The General Ledger extracts details
class general_ledger_costs(Base):
    '''
    The General Ledger costs, as extracted for this extraction, for this hospital
    '''
    __tablename__ = 'general_ledger_costs'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class itemized_costs(Base):
    '''
    Individual item costs from service providers who provide services or items to patients and who provide itemized bills
    which identify the hospital servcie and episode_no associated with the specific service or item.
    '''
    __tablename__ = 'itemized_costs'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    service_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    who:Mapped[str] = mapped_column(String(50), primary_key=True, autoincrement=False)
    invoice_no:Mapped[str] = mapped_column(String(20), primary_key=True, autoincrement=False)
    invoice_line_no:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    item_date:Mapped[datetime.date] = mapped_column(Date, nullable=False)
    episode_no:Mapped[int] = mapped_column(Integer, nullable=False)
    what:Mapped[str] = mapped_column(String(50), nullable=True)
    department_code:Mapped[str] = mapped_column(String(12), nullable=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), nullable=False)
    amount:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        Index(None, 'hospital_code', 'run_code', unique=False),
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'service_code'], ['services.hospital_code', 'services.service_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class general_ledger_run_adjustments(Base):
    __tablename__ = 'general_ledger_run_adjustments'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    from_department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    from_cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    to_department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    to_cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    mapping_order:Mapped[int] = mapped_column(Integer, nullable=True)
    mapping_type_code:Mapped[str] = mapped_column(String(1), nullable=True)
    amount:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'from_department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'from_cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
        ForeignKeyConstraint(['hospital_code', 'to_department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'to_cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )


# The Clinical Costing modelling configuration tables
class models(Base):
    '''
    The code and name of each Clinical Costing model
    (Can be used for more than one hospital)
    '''
    __tablename__ = 'models'
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_description:Mapped[str] = mapped_column(String(50), nullable=True)

class mapping_types(Base):
    __tablename__ = 'mapping_types'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    mapping_type_code:Mapped[str] = mapped_column(String(1), primary_key=True, autoincrement=False)
    mapping_type_code_description:Mapped[str] = mapped_column(String(50), nullable=True)

class general_ledger_mapping(Base):
    __tablename__ = 'general_ledger_mapping'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    from_department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    from_cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    to_department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    to_cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    mapping_order:Mapped[int] = mapped_column(Integer, nullable=True)
    mapping_type_code:Mapped[str] = mapped_column(String(1), nullable=True)
    amount:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'from_department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'from_cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
        ForeignKeyConstraint(['hospital_code', 'to_department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'to_cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class general_ledger_mapped(Base):
    __tablename__ = 'general_ledger_mapped'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class department_grouping(Base):
    __tablename__ = 'department_grouping'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    from_department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    to_department_code:Mapped[str] = mapped_column(String(12), nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'from_department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'to_department_code'], ['departments.hospital_code', 'departments.department_code']),
    )

class cost_type_grouping(Base):
    __tablename__ = 'cost_type_grouping'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    from_cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    to_cost_type_code:Mapped[str] = mapped_column(String(12), nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['model_code'], ['models.model_code'], name='FK:COST_TYPE_GROUPING->MODELS'),
        ForeignKeyConstraint(['hospital_code', 'from_cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
        ForeignKeyConstraint(['hospital_code', 'to_cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class department_cost_type_grouping(Base):
    __tablename__ = 'department_cost_type_grouping'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    from_cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    to_cost_type_code:Mapped[str] = mapped_column(String(12), nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'from_cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
        ForeignKeyConstraint(['hospital_code', 'to_cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class general_ledger_built(Base):
    __tablename__ = 'general_ledger_built'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class event_class_codes(Base):
    __tablename__ = 'event_class_codes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_class_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_class_seq:Mapped[float] = mapped_column(Float, nullable=True)
    event_class_description:Mapped[str] = mapped_column(String(50), nullable=True)

class event_cost_type_codes(Base):
    __tablename__ = 'event_cost_type_codes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_cost_type_description:Mapped[str] = mapped_column(String(50), nullable=True)

class event_cost_sub_type_codes(Base):
    __tablename__ = 'event_cost_sub_type_codes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_cost_sub_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_cost_sub_type_description:Mapped[str] = mapped_column(String(50), nullable=True)

class event_source_codes(Base):
    __tablename__ = 'event_source_codes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_source_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_source_description:Mapped[str] = mapped_column(String(50), nullable=True)

class event_codes(Base):
    __tablename__ = 'event_codes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_code_description:Mapped[str] = mapped_column(String(50), nullable=True)
    event_class_code:Mapped[str] = mapped_column(String(12), nullable=True)
    event_cost_type_code:Mapped[str] = mapped_column(String(12), nullable=True)
    event_cost_sub_type_code:Mapped[str] = mapped_column(String(12), nullable=True)
    event_source_code:Mapped[str] = mapped_column(String(12), nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'model_code', 'event_class_code'], ['event_class_codes.hospital_code', 'event_class_codes.model_code', 'event_class_codes.event_class_code']),
        ForeignKeyConstraint(['hospital_code', 'model_code', 'event_cost_type_code'], ['event_cost_type_codes.hospital_code', 'event_cost_type_codes.model_code', 'event_cost_type_codes.event_cost_type_code']),
        ForeignKeyConstraint(['hospital_code', 'model_code', 'event_cost_sub_type_code'], ['event_cost_sub_type_codes.hospital_code', 'event_cost_sub_type_codes.model_code', 'event_cost_sub_type_codes.event_cost_sub_type_code']),
        ForeignKeyConstraint(['hospital_code', 'model_code', 'event_source_code'], ['event_source_codes.hospital_code', 'event_source_codes.model_code', 'event_source_codes.event_source_code']),
    )

class event_attribute_codes(Base):
    __tablename__ = 'event_attribute_codes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_attribute_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_attribute_description:Mapped[str] = mapped_column(String(50), nullable=True)

class event_attributes(Base):
    __tablename__ = 'event_attributes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_attribute_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    event_subroutine:Mapped[str] = mapped_column(String(12), nullable=True)
    event_what:Mapped[str] = mapped_column(String(12), nullable=True)
    event_where:Mapped[str] = mapped_column(String(12), nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'model_code', 'event_code'], ['event_codes.hospital_code', 'event_codes.model_code', 'event_codes.event_code']),
        ForeignKeyConstraint(['hospital_code', 'model_code', 'event_attribute_code'], ['event_attribute_codes.hospital_code', 'event_attribute_codes.model_code', 'event_attribute_codes.event_attribute_code']),
    )

class general_ledger_attribute_codes(Base):
    __tablename__ = 'general_ledger_attribute_codes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    general_ledger_attribute_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    general_ledger_attribute_description:Mapped[str] = mapped_column(String(50), nullable=True)

class general_ledger_attributes(Base):
    __tablename__ = 'general_ledger_attributes'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    general_ledger_attribute_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    general_ledger_attribute_weight:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
        ForeignKeyConstraint(['hospital_code', 'model_code', 'general_ledger_attribute_code'], ['general_ledger_attribute_codes.hospital_code', 'general_ledger_attribute_codes.model_code', 'general_ledger_attribute_codes.general_ledger_attribute_code']),
    )

class general_ledger_disbursement(Base):
    __tablename__ = 'general_ledger_disbursement'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    disbursement_level:Mapped[int] = mapped_column(Integer, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class general_ledger_disbursed(Base):
    __tablename__ = 'general_ledger_disbursed'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    run_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['hospital_code', 'run_code'], ['clinical_costing_runs.hospital_code', 'clinical_costing_runs.run_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )

class general_ledger_distribution(Base):
    __tablename__ = 'general_ledger_distribution'
    hospital_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    model_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    department_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    cost_type_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    distribution_code:Mapped[str] = mapped_column(String(12), primary_key=True, autoincrement=False)
    distribution_weight:Mapped[float] = mapped_column(Float, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['hospital_code'], ['hospitals.hospital_code']),
        ForeignKeyConstraint(['model_code'], ['models.model_code']),
        ForeignKeyConstraint(['hospital_code', 'department_code'], ['departments.hospital_code', 'departments.department_code']),
        ForeignKeyConstraint(['hospital_code', 'cost_type_code'], ['cost_types.hospital_code', 'cost_types.cost_type_code']),
    )
