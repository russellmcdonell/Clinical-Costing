# How to calculate clinical costs
## Installation
If you are using Visual Studio Code then you can just clone this repository.
If not, then download all the Python scripts (including those in the tools folder), all the example Excel workbooks
from the hospitalActivity/hospital1, hospitalCost/hospital1, hospitalConfig/hospitals, hospitalConfig/models folders
and the database connection configuration file from the databaseConfig folder. Download the launch.json from the .vscode
folder. This will show the order in which the script need to be run and the command line arguements for each.
Edit the 'clincal_costings.json' file with the required parameters to connect to your database.
The **Clinical Costing System** uses Python's SQLAlchemy module for database interactions, so any database compatible
with SQLAlchemy should work. All the code has been tested using a MySQL database server.

You are now ready to compute the clinical costs for the example hospital (hospital1) with the example clinical costing model (model1)
for the clinical costing period of Jun-1997. The database will need to exist; you may need to get a database administrator to create it.
Initially, the database should have no tables. THe 'tools/createSQLAlchemyDB.py' script will create all the tables, all the indexes and
all the foreign keys. The 'tools/defineSQLAlchemyDB.py' script contains all the definition of the database schema.
This schema matches the example data; specifically the 'hospital1' hospital, the 'model1' clinical model
and the hosptial1 Patient Activity and Clinical Costs extracts.

The database schema is quite strict; codes in the data must match codes in the associate code/description tables.
This limits the risk of costs getting lost; if you create an new department in the general ledger then the data won't load
until the department code and department description is added to the 'departments' table. Similarly, if your hospital
opens a new ward, or changes the codes/names of the wards. Of course just adding the code won't prevent costs being lost;
you'll need to adjust the clinical costing model to ensure that the cost associated with new departments are disburse
or distributed and you'll need to ensure that clinical costing events are created for any new wards or clinics.

The strictness of the database model does increase the amount of maintenance that is required
to keep the **Clincal Costing System** running. Fortunately there are scripts that allow you to quickly reload the
hospital definition and the clinical costing model definition. Those script will add new codes and update the
descriptions of any existing codes, but will not delete anything. So you can re-run them with, new data, if you've missed something.
There is one restriction - you cannont change the case of a letters in a code. If you configure "Ward 3" with the code 'w3',
then you can't change that code code to 'W3'. If you need to delete codes, or if you must change the case of a code,
then the best strategy is to create an new, empty database and load everything. Or you could create a new hospital code.
Or you could create a new clinical model code. And if this is a test environment, you can get a database administrator
to drop all the table and then use 'createSQLAlchemyDB.py' to re-initialize the database.

Ideally, the database schema will need very little changing. However, the tables in the database must match
sheet names in the Excel workbooks, and the column headings in those sheets must match the column names of the columns
in the matching table. Usually, it is easier to modify the extracts to match the database, rather than modifying
the database to match the extracts. For inpatients there will be an extract containing 'bed days'.
Making 'bed_days' the heading for that column in the extract is a lot easier than changing the database schema
and all the associated code.

Database schema modification are possible. The database schema in 'tools/defineSQLAlchemayDB.py' is easy to read and understand.
It is likely that you will want to make changes to facilitate better, more detailed, clinical costing reporting.
For instance, the tables relating to Patient Activity may need updating/tweaking because
you use a different inpatient condition classifier; something other than DRG.
Or you may wish to collect additional Factors (dimensions) that will only be used in the clinical costing reports.
Those sorts of changes can easily be accomodated by changing column names and adding additional columns to tables.
As long as you are not touching primary keys you will have no difficulty making those sorts of changes.

You can create new clinical costing events, based upon the new Factors (dimensions) by simply updating the clinical costing model;
specifically the 'where' clause associated with these new clinical costing events.

You can also add additional Quantities (measures) and create new clinical costing events base upon those new Quantities (measures).
However, this will require both configuration and code changes. The script 'build_events_functions.py' contains
all the functions for building clinical costing events, as configured in the clinical costing model. New clinical costing events,
based upon new Quantities (measures) will require new functions, which can be crafted by copying and modifying/tweaking
one of the existing functions.

Similarly, you may create entirely new Patient Activity extract, such as patient location within the Accident and Emergency department,
to track patient movements. Or a complete set of Mental Health Patient Activity extract to support the clinical costing
of you Mental Health Service. Here you will need to create new tables in 'tools/defineSQLAlchemyDB.py'. The existing tables
can be used a models of how to do this, but you will also have to create new 'build_event_functions.py' functions.

**NOTE:** The **Clinical Costing System** does not support database re-design. Any changes to 'tools/defineSQLAlchemyDB.py'
will require the creation of a new, blank database, so that 'tools/createSQLAlchemyDB.py' can create new, empty tables.
The database can be modified by a database administrator, with 'tools/defineSQLAlchemyDB.py' updated as documentation
of the new, current design, but extreme caution is recommended. Only be creating a new database and using 'tools/createSQLAlchemyDB.py'
can you guarantee that the actual database matches the design.

## Configuration
### The Hospital
Each hospital will have a hospital code and name and some characteristics that are unique to this hospital
* The general ledger will have departments (cost centres) and cost types (subjectives). You will need to configure some
additional psuedo cost types to hold temporary costs or grouped cost types. You may need to configure some
additional pseudo departments to hold amalgamated department costs where multiple departments can be seen as
providing the same support/overhead services.
* The hospital will provide Services, which are major patient care activites associated with the largest of the patient administration
applications, such as Inpatient services, Outpatient (Clinic) Service, Accident and Emergency Services, etc.
* The hospital will have wards and theatres and may run clinics.
* The hospital will employ clinician. Here it is sometimes useful to pseudo clinician, based upon roles or positions
that may be filled by different people from time to time, such as registrars who may be a rotating postion.
* Where possible, additional clinical costing information should be brought in from other systems which are
generically called 'feeder' systems. Such 'feeders' are often data from itemized invoices and must identify the episode of care
to which the item applies. Some 'feeders' will have actual costs, which have already been brought into the general ledger accounts.
Others will have indications (weights) of the relative costs of the items in the 'feeder' data.
### The Clinical Costing Model
It is possible to look a clinical costs from many different angles. The grouping and assignment of costs can vary, depending upon
the focus of the intended reports. The clinical costing model for internal reporting may vary from a clinical costing model
intended for benchmark comparisions against other hospitals. Hence, there can be multiple clinical costing models for each hospital.
#### Indirect Costs
The first step is to identify which departments are truely 'indirect'; their costs cannot be allocated
to specific clinical care activities. The remaining departments will be 'direct' accounts and their costs will be allocated to episodes of care.
Sometime that allocation will be 'generic' for all instance of a particular cost type, such as 'Laundry' which represents
the cost of clean sheets after a patient is discharged. All wards will have a 'Laundry' cost type.
However, that same cost type may exist in an 'indirect' department, such as the Kitchen where 'Laundry' is the cost of providing
madatory clean uniforms for the Kitchen staff. Cases such as this will require the mapping of that cost type in the 'indirect'
department to a new/pseudo cost type. For instance, Kitchen/Laundry can be mapped to Kitchen/other. Kitchen/Laundry
should not be assigned to episode care where the patient was discharged. Rather, an 'indirect cost' disbursement of
Kitchen/other will be configured to handle these costs.

Often there are similar departments, especially 'indirect' departments, which will be disbursed in the same way.
And often it is not necessary to track these costs back to the original department. If this is the case, then it
makes sense to group these similar departments into a single new/pseudo department

Similarly, there are often cost types which exist in the general ledger purely for general ledger reporting or for reasons
of accounting standards, but which, from a clinical costing perspective, represent a common concept. If this is the case, then it
makes sense to group these similar cost types into a single new/pseudo cost type the better reflect this common concept.

##### Indirect Cost Disbursement
The costs in 'indirect' departments have to be disbursed to 'direct' departments, ususally into a holding cost type of 'overheads'.
This disbursal is somewhat arbitrary, but it is possible to find valid models for this disbursement. For instance, if a department
provides cleaning services to other departments, then it is likely that they spend more time, at a higher cost, cleaning the departments
that have more floor space. You may be able to get an extimate of how much power each department uses for a specific month.
Those figures can be use as the disbursement weights for power going forward, on the assumption that there are no significant
changes in the infrastructure. These disbursement 'weights' are called 'attributes' and each department can have, and will have,
multiple 'attributes'. Some 'indirect costs' (indirect department/cost type) will be disbursed based upon all the departments
that have a particular 'attribute', proportionally based upon the size of that 'attribute'. Other 'indirect costs' will be
disbursed based upon all the departments that have a different 'attribute'.

#### Direct Costs
All the 'direct costs' (direct department/cost type) have to distributed to episodes of care. However, different 'direct costs'
have to be distributed to episodes of care based upon different aspects. Not all episodes of care have all the same aspect.
Not all patients are discharged during the clinical costing period. Not all patients go to Theatre.

To identify where 'direct costs' should be distributed, the **Clinical Costing System** builds clinical events.
A clinical event is a snippet of an episode of care, of only those episodes of care that have one specific attribute.
For instance you may configure a clinical event for all patients admitted under the 'Opthomology' clinical specialty.
Opthomolgy costs would then be distributed to these, and only these, episode of care.

##### Direct Costs - Clinical Events
Configuring a clincal costing event starts with the selection of a clinical event subroutine. Each clincial event suburoutine
select one Quantity (measure) from one Patient Activity extract table to build clinical costing events of a specified type (event code).
To configure a clinical event you have to specify an event code, a clinical event subroutine an optionally a event 'where' clause.
The event 'where' clause is an SQL WHERE clause that selects a subset of all the episodes of care normally selected by
the clinical event subroutine. For example, for 'food' events you would configure an event 'where' clause that did not
select bed days in the Day Procedures Unit, because patients in the Day Procedures Unit don't get fed.

The other things you can configure are
* Event Attribute Base - a number to be added to the computed event weight for cases where the correct with is something like 'bed days plus 1'
* Event Attribute Weight - a scaling factor for the computed weight. You can configure the same clinical event more than once,
with the event 'where' clause used to select distint subsets and the event 'attribute weight' used to reflect the different
significance of each subset. For example, patients in in all the other wards may get fed more food (attribute weight 3.3)
than patients in the Limited Care Dialysis Unit (attribute weight 1.0) and patient in the Day Procedures Unit (attribute weight 0.0).
* Event Acuity Scaling - some Patient Activity extract may have an associated acuity value. For instance, the hospital may have
a patient and nurse dependency application so every patient bed day has an acuity value reflecting the average nursing load
for that patient over the bed days. This is relevant when creating nursing clinical events (acuity scaling 1.0), but
irrelevant for overhead costs (acuity scaling 0.0).

### Direct Costs - Distribution
The final thing to configure is which accounts will be distributed to which clinical events.
Sometimes it is necessary to distribute one account over two different clinical events, such a registrar's salary
distributed over patient bed days (for ward rounds) and patient discharges (for writing discharge summaries).
To support this, each configured distribution has a 'distribution fraction'. It is import that these 'distribution fractions' add
up to 1.0 for any account that is distributed over more than one clinical event. If not, some fraction of the account costs
will remain undistributed.

## Loading the data for each Clinical Costing Run
### Patient Activities
The worksheets in the Patient Activity extract Excel workbook must match the Patient Activity tables in the database.
The worksheet name for each database table is configured as a dictionary in the 'load_hospital_activity.py' script.
The headings in each worksheet have to match the column names in tables into which this data will be loaded,
with the exception of 'hospital_code' and 'run_code' which will be prepended to each row.
The data type of the data in the columns under each heading must match the data type of the matching column in the database.
If these things don't match then you may have to go back and reconfigure the database schema.

### Hospital Costs
Again, the 'general ledger costs' worksheet must match the 'general_ledger_costs' table in the database; matching column names, matching data types,
with the exception of 'hospital_code' and 'run_code' which will be prepended to each row.
The 'feeder' data (itemized costs) is loaded from worksheets in the same Excel workbook as the general ledger costs.
A single worksheet (itemized costs) list the feeder data to be loaded, both the worksheet containing the data and the feeder code for that data.
The data in these 'feeder' data worksheets must match the 'itemized_costs' table in the database; matching column names, matching data types,
with the exception of 'hospital_code' and 'run_code' which will be prepended to each row.
will be loaded (general_ledger_costs, itemized_costs, general_ledger_run_adjustments and gl_atribute_adjustments).

Two types of run-time adjustments can be configured for each clincal costing run.
* general_ledger_run_adjustments - these are non-itemized costs that can vary from clinical costing run to clinical costing run.
They reflect non-itemized costs that come from other systems, such as payroll, and which are already included in the general ledger costs,
but which should be clinically costed separately. Hence the general_ledger_run_adjustments are an additional general ledger mapping table.
* gl_attribute_adjustments - these reflect changes within the hospital, for this clinical costing period, such ward where beds have
been closed and hence floor space has been reduced. However, if the changes are significant, such as reconfiguring the hospital to
handle a pandemic, then you may need to craft a new clinical costing model as a modified clone of the current model.

## Computing the Clinical Costs
## Build the costs
The 'build_costs.py' scripts massages the general ledger costs for a specific hospital, for a specific clinical costing run according the
general ledger mapping and grouping for a specific clinical costing model, plus any run specific adjustments for this clincial costing run.
This prepares the general ledger costs, ready for disbursement and distribution.
The total costs for this clinical costing run are reported a various stages in this process.
These 'total cost' values should all be identical. If not, there is something wrong with the clinical costing model and some costs
are not being catered for and are getting 'lost'.

The database table 'general_ledger_costs' contains the genaral ledger costs before the 'build_cost.py' script was run. This table constains the
general ledger costs 'as loaded' and will remain unchanged, even if the 'build_costs.py' script is re-run.

The following database tables can be used to help diagnose any issues with the way the clinical costing model is transforming the general ledger costs.
* 'general_ledger_adjusted' contains the general ledger costs after the 'build_costs.py' script
has performed any adjustments for cost based 'feeder' data.
This table is cleared and rebuilt (for a specific hospital, specific clinical costing run, specific clinical costing model) each time
the 'build_costs.py' script is run.

* 'general_ledger_mapped' contains the adjusted and mapped general ledger costs after the 'build_costs.py' script
has performed any required mapping to the adjusted general ledger costs.
This table is cleared and rebuilt (for a specific hospital, specific clinical costing run, specific clinical costing model) each time
the 'build_costs.py' script is run.

* 'general_ledger_built' contains the adjusted, mapped and grouped general ledger costs after the 'build_costs.py' script
has performed any required grouping to the adjusted and mapped general ledger costs.
This table is cleared and rebuilt (for a specific hospital, specific clinical costing run, specific clinical costing model) each time
the 'build_costs.py' script is run.

## Disburse the 'indirect' costs
The 'disburse_costs.py' script disburses the 'indirect cost' accounts for a specific hospital, for a specific clinical costing run according to
a specific clinical costing model.
This script reports the 'total costs', the amount of 'indirect costs'
and the 'total costs' after disbursement. Again, the 'total costs' at the start should match (or nearly match - see below) the 'total costs'
after disbursement. If the 'indirect costs' appear unreasonably large or the 'total costs' before disbursement does not match (approximately)
the 'total costs' after disbursement, there there is something wrong with the configuration of the clinical costing model.

By default the 'disburse_costs.py' script disburses the 'indirect costs' using the Cascade disbursement method. Using this method all the 'indirect costs'
must be disbursed and the 'total cost' before disbursement must exactly match the 'total costs' after disbursement.
It is advisable to run the Cascade disbursement method as an initial test of the configuration.

The 'disburse_costs.py' script takes on optional arguement (-i) which changes the disbursement method from Cascade to Iteration.
The Iteration disbursement method could disburse all the 'indirect costs', but each iteration only disburses most of the 'indirect costs'.
The fraction that remains undisbursed decreases each iteration. However, iterating until that fraction reaches zero could take for ever.
Currently the 'disburse_costs.py' script stops iterating when there is less than $0.05 of 'indirect costs' remaining undisbursed.

The following database tables can be used to help diagnose any issues the with way the clinical costing model is disbursing the 'indirct' costs.
* 'general_ledger_built' contains the 'as built' costs.

* 'general_ledger_disbures' contains the 'as built' general ledger costs after the 'disburse_costs.py' script has disbursed 'indirect costs'.
This table is cleared and rebuilt (for a specific hospital, specific clinical costing run, specific clinical costing model) each time
the 'disburse_costs.py' script is run.


## Build the clinical costing events
The 'build_events.py' script builds the clinical costing events for a specific hospital, for a specific clinical costing run according to
a specific clinical costing model. These clinical costing events are the place holders to which the 'direct costs' will be distributed.

## Distribute the 'direct' costs
The 'distribute_cost.py' script distributes the 'direct cost' accounts after disbursement, for a specific hospital,
for a specific clinical costing run according to a specific clinical costing model,
to the clinical costing events created by the 'build_events.py' script.

The computed clinical costs are created in the 'event_costs' database table.
All clinical costing reports should be run against this table.

The database table 'event_costs' contains the columns 'hospital_code', 'run_code', 'model_code', 'service_code' and 'episode_no'
to facilitate joining back to the Patient Activity table for reports that require specific Factors (dimension) from those tables.
The column 'event_seq' has been copied from the matching sequence column, if present, in the Patient Activity table.
Hence, to join back to the 'inpat_patient_location' Patient Activity table, you would include the additional JOIN clause
of "event_costs.event_seq = inpat_patient_location.location_seq".
