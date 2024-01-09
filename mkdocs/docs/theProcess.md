# The Clinical Costing Process
The Clinical Costing Process consists of a number of step, some of which are executed once,
others are repeated, every clinical costing period.

## The "One Off" processes
These step are only executed when you are configuring up the **Clinical Costing System** for a new hospital,
or a new clinical costing model for a hospital.

### Configuring a database connection
The folder 'databaseConfig' contains the database connections definitions file (clinical_costing.json).
In this configuration file you create a "name" for each database and the definitions, used by SQLAlchemy, when connecting to, and accessing, that database.

* "connectionString" - the connection string use by SQLAlchemy to connect to this database [required].
* "user" - the username used by SQLAlchemy for connecting to the database [required].
* "passwd" - the user password used by SQLAlchemy for connecting to the database [required].
* "server" - the server and port used by SQLAlchemy for connectin to the database server [required].
* "databaseName" - the name of the database [optional]. If not supplied, SQLAlchemy will use the default database for this server.


### Creating a database

#### ::: createSQLAlchemyDB

The script 'tools/createSQLAlchemyDB.py' uses the configuration file 'tools/defineSQLAlchemyDB.py' to create all the tables, 
indexes and foreign keys required by the **Clinical Costing System**. The script 'tools/defineSQLAlchemyDB.py' does define the structure
of every patient activity extract which also defines how your clinical costs are going to be reported/analysed. You may need to make
modifications to those tables to match your extracts. For instance, you may chose to include DRG in the extract for inpatient episode of care
so that you can compare costs, by DRG, with other hospitals. A database administrator could make these sorts of modifications,
after the database is built, but it is probably better to update 'tools/defineSQLAlchemcyDB.py' and build a new database.
The **Clinical Costing System** uses SQLAlchemy because of the ease with which tables can be defined and modified.
The intent in the design is to enable the clinical costing administrator to control the process.

### Configuring a hospital

#### ::: load_hospital

The 'load_hospital.py' script loads the code/description pairs for specific concepts which are unique to a specific hospital, from an Excel workbook.
The worksheet 'hospital' contains a code/description pair for this hospital. If this definition already exists in the database, then the following
worksheets will be considered 'updates'; that is new code/descriptions will be added and descriptions will be updated for existing codes,
but no existing code/description pair will be deleted, as they may have been used in exiting clinical costing runs.
The hospital specific Excel workbook will contain the following hospital specific worksheets.
    . feeder types and feeders - cost come from the general ledger, in a general ledger extract. However, the general ledger can be
quite a blunt instrument for assigning costs. Sometimes other sources of costing information can be much more granular and provide
better specificity. For instance, pathology and radiology services may be outsourced, and the service provider may provide itemized invoices
listing the patient, date of service and item cost. These costs can be attributed to those specific patients, but these same costs are already
included in the general ledger extract in a single account, possibly bundled in with other cost into a single figure.
Feeders provide a mechanism for removing these costs from the larger general ledger account and creating
clinical costing events for each item, with the item cost, associated with the exact patient episode of care.
This type of feeder is called a 'Cost' feeder.

Sometimes the event is known, but not the exact cost. For instance the theatre system may know exactly which patients received which prosthetic,
and the accounts receivable system may know the amount that would be charged to a private patient, for each prosthetic.
But that amount is not a cost, just a good, weighted estimate; larger amounts imply more expensive prosthetics.
Howver, the supply department may know the value of prosthetics purchased during the clinical costing period.
This is a cost, but it is a single amount and is not specific to any particular patient.
Further more, that cost is already included in the general ledger extract, and my be bundle in with other theatre costs such as other medical supplies.
The extract from the theatre system is an 'Amount' feeder, which provides a mechanism for creating 'prosthetic' clinical costing events
with the 'amount' as a weight. The cost figure from the supply deparment is removed from the more general theatre 'medical supplies'
general ledger account and moved into a new/pseudo account, which is later distributed across all the 'prosthetic'
clinical costing events, according to the weight of each of those 'prosthetic' events.

* departments/cost types - departments (sometimes call 'cost centres') and cost types (sometimes call subjectives) come from the general ledger.
These code/descriptions are used to check the general ledger extract and pick up any new departments or cost types that have been created since
the last clinical costing run, but which clearly have not been catered for in the current configuration.

* services - are the major services provided by the hospital, such as inpatients, clinics and accident and emergency services. These services
are associated with the patient administration application from the the Patient Activity extract will be taken.

* wards - are the inpatient hospital wards and each is usually associated with a group of general ledger accounts. The codes are the codes that
can be found in the inpatient Patient Activity extracts, and will be use to match the associated activities with the ward's general ledger costs.
The ward codes are used to check the inpatient Patient Activity Extracts and pick up any wards that have been created since the last clinical
costing run, but which clearly have not been catered for in the current configuration.

* theatres - are the hospital's theatres and are usually associated with a single group of general ledger accounts for all the theatres.
These codes are the codes that can be found in the Theatre Activity extracts, and will be use to match the associated theatre activities
with the theatre general ledger costs. The theatre codes are used to check the theatre Patient Activity Extracts and pick up any theatre
that have been created since the last clinical costing run, but which clearly have not been catered for in the current configuration.

* clinics - are the outpatient hospital clinics and each is usually associated with a group of general ledger accounts. The codes are the codes that
can be found in the outpatient Patient Activity extracts, and will be use to match the associated activities with the clinic's general ledger costs.
The clinic codes are used to check the outpatient Patient Activity Extracts and pick up any clinics that have been created since the last clinical
costing run, but which clearly have not been catered for in the current configuration.

* clinicians - is a full list of all clinicians that may be associated with patient activity, be it inpatient, outpatient
or accident and emergency activity. The clinician codes are used to check the Activity Extracts and pick up any clinicians that
have commenced work at the hospital since the last clinical costing run, but which clearly have not been catered for in the current configuration.

### Configuring a model

#### ::: load_model

The 'load_model.py' script load a specific clinical costing model, for a specific hostpital,
that can be used to compute the clinical costs for any clinical costing run.
Clincal costing modelling is where the art of clinical costing is most evident.
It is a three part process

1. reshaping the general ledger into a more appropriate set of accounts.
2. building clinical costing events from the Patient Activity extracts.
3. assigning the costs, reshaped in step 1, to the clinical costing events built in step 2.

However, the configuration of all three parts is conceived/imagined collaboratively.
Clinical costing events are subset of the Patient Activity data, identifying specific activities to which specific costs can be assigned.
Sometimes it is the same data, given different semantic meaning, for the assignment of different types of costs.
For instance, inpatient bed days can be a 'nursing' event for the distribution of ward nursing costs.
However, those same bed days can be a 'medical' event for the assignment of medical costs for doctors doing ward rounds.

##### Indirect Cost Modelling
The aim here is to identify which general ledger accounts can be deemed 'direct cost' account; that is, accounts for which clinical costing events
can be built, ready for the assignment of those costs. All the remaining accounts will be classified as 'indirect' and will also be allocated to
clinical costing events, but using a very crude allocation and clearly identified as 'overheads'.
The definition of 'direct' is sometimes fuzzy or vague and sometimes it requires an additional Patient Activity extract or a new feeder extract.
For instance, the Medical Records department can be thought of as an 'overhead', but there are specific Medical Records activities
that can be directly linked to the delivery of care to patients; Medical Records is involved in the admission and discharge of patients.
Patient Activity extracts of patient admitted during the clinical costing period and patient discharged during the clinical costing period
would enable the construction of 'Medical Records' clinical costing events. Discharges could be used to create 'medical discharge summary'
clinical costing events and medical costs could then be split, with some allocated to 'ward rounds' based upon the 'medical bed days' clinical costing events
and some allocated to 'creating discharge summaries' based upon the 'medical discharge summary' clinical costing events.

It all starts with re-shaping the general ledger extract into a set of accounts that better fit the clinical costing requirements.
We start by dealing with the cost based feeder costs. Each feeder extract item will identify the general ledger account where each cost has been recorded.
The feeder costs will need to be subtracted from these specified general ledger accounts, as the item costs will be directly assigned
to 'feeder' clinical costing events. To keep the general ledger balanced, these costs will be moved to a new/pseudo account.
These new/pseuco accounts will be zeroed when the feeder clinical costing events, with their associated feeder costs, are created.

Next we map the general ledger extract; moving costs from one department/cost type to a different department and/or cost type.
Sometimes this is done simply to change the description of a cost to something more meaningful. For instance, after subtracting the feeder costs
from the associated general ledger account there may be some residual costs. These will be period differences; possibly costs from a different
clinical costing period or adjustments. Hence, these costs have a different semantic meaning and moving them to a different cost type will make
this clearer in any clinical costing report. Sometimes a general ledger cost type has different semantic meanings in different general ledger departments
and has to be treated differently in those different contexts. For instance, 'drugs' is an internal cost associated with medications
delivered from the pharmacy to different departments. For the wards these will be medications given to patients.
Hence 'drugs' will be distrubted to patients based on something like bed days.
However, for the Kitchen, these 'drugs' are for the Kitchen first aid kit and are things like headache tables taken by Kitchen staff.
In this scenario it make sense to map Kitchen/drugs to Kitchen/other, as it is really an overhead cost associated with the running of the Kitchen.

Next we group 'like' departments together which simplifies the general ledger. Departments that provide support services are
an obvious candidate. None of these departments are going to be distributed directly to patient events, but rather distributed to all patients
as an overhead. Hence, grouping them into a single pseudo 'Support' department simplifies any clinical costing analysis. Departments that only
support nursing functions can be grouped into a single pseudo 'Nursing Support' department that can be assigned as an overhead to nursing
clinical costing events.

Next we simplifying groups of cost types for specific departments. For instance, the general ledger may distinguish
between 'salary and wages', 'superannuation' and 'workcover insurance'. For deparments that deliver direct patient care, those things
are important as a whole, but not individually and they can be grouped into a single cost type of 'wages'.
For indirect/overhead departments they are just another overhead cost and can be grouped with other cost types into a single cost type of 'other'.

The final general ledger reshaping task it so group small groups of similar cost type together into a new, single pseudo cost type.
For instance, 'salary and wages', 'superannuation' and 'workcover insurance' can be grouped into a single cost type of 'wages'
as clinical costing does not need to distinguish between these.

All of this general ledger mapping and reshaping it configured as part of the clinical costing model.
The **Clinical Costing System** will then group any cost type not specifically mentioned/configured above into a single cost type of 'other'
for every department. Hence, it is important to clearly identify what cost are going to remain identifyable in the final clinical costing data.

At this point all the 'direct cost' accounts have been identified and everything else has been classified as an 'indirect cost' account.
More importantly, 'direct' patient care departments will have been identified, with all other departments being classified as 'indirect'.
All of the costs in the 'indirect' accounts will be disbursed to other departments into new/pseudo 'overheads' cost types.
For this to happen, a basis for disbursing these 'indirect' accounts must be configured, with the departments to which
these 'indirect' costs will be disbursed.

To disburse these 'indirect' accounts, new/psudo 'overheads' account will be created in each department receiving 'indirect' costs
and those new/pseudo 'overheads' accounts will be configured with 'attributes'.
These 'attributes' are weights for the proportional disbursement of the 'indirect' costs.
As an example, the Maintenance department maintains building and is an 'indirect' department. A reasonable basis for this disbursement
may be 'floor space'. A departments/'overheads' accounts would be configured for all departments in buildings maintained by the Maintenace department,
with their floor space as the 'attribute'. Other possible 'attributes' are "count of PCs" or "garden area".
For some thing the actual amount spent in the clinical costing period is a better 'attribute'.
Any department department 'attribute' where the attribute code starts with the letters 'total' will have the attribute value
updated by the **Clinical Costing System** to the total costs for the clinical costing period. This makes sense for things like the Accounting department
which can be disburse over the 'total' attribute. However, you can have 'totalNursing' as an 'attribute' that is only assigned to the wards.
And you could disburse the 'Nursing Support' costs over the 'departments' which have a 'totalNursing' 'attribute'.

Also, any 'attribute' with an attribute code that starts with the letters that match an existing 'cost type'
will have the value of that 'attribute' updated to the matching cost, for that 'cost type', for the clinical costing period.
Again, wards could have an 'attribute' of 'wagesNursing' and the Payroll department can be split into 'nursing' and 'other' costs,
with 'nursing' cost disbursed to 'departments' with the 'wagesNursing' 'attribute'.

Whilst this does seem logical and fair, it does create problems. Fistly, the Cleaning Service department provides cleaning services
to both 'direct' and 'indirect' departments; cleaning wards around beds and cleaning offices. The Cleaning Services cost can be disbursed
based upon floor space, but for the Cleaning Services cost disbursed to wards has to be kept separate from 'overheads'
in a 'direct' account that will be distributed later, base up bed days.
The assumption is that Cleaning Services doesn't clean around empty beds, so ward bed days is being used as a proxy
to distribute Cleaning Services, provided to the wards directly to episodes of patient care.

To achieve this, all 'indirect departments' that are cleaned by the Cleaning Services department are configured with
a department/'overheads' account, with a 'housekeeping' attribute, with the value of that attribute being the floor space for that department.
All the ward are configured with a ward/'housekeeping' account, with a 'housekeeping' attribute, with the value of that attribute being the floor space for that ward.
Departments that don't get cleaned by the Cleaning Services department, because they do their own cleaning, such as Theatres, would have a floor space attribute,
but would not have a 'housekeeping' attribute. Now the Cleaning Services costs can be disbursed, based upon this 'housekeeping' attribute.

However, there is a second problem; the Accounting department's costs will be disbursed, based upon the 'total' expenditure atttribute
for each department, with some costs going to the Cleaning Services department, which will have a 'total' expenditure attribute.
And the Cleaning Services department's costs will be disbursed, based upon the 'floor space' attribute for each department,
including the Accounting department which will have a 'floor space' attribute.
In fact, the Accounting department will also have a 'total' expenditure 'attribute', so some Accounting department costs will be
disbursed back to the Accounting department. The aim of 'indirect' disbursement is to move all the 'indirect overhead' costs
to the 'overheads' cost types in 'direct' patient care departments. On the surface, that seems hard to do with just 'attributes' as the basis
for 'indirect' disbursement.

There are two strategies for handling this problem. One strategy is to create an heirarchy, with the 'most indirect'
account (department/cost type) being disbursed first, and the 'least indirect' account (department/cost type) being disbursed last
and creating a rule that no costs can be disbursed to an account (department/cost type) whose costs have already been disbursed.
This is called the 'Cascade' strategy. For instance, at level 1 you would disburse 'indirect costs' that are overheads to the 'overheads' cost types
and disburse 'direct costs' from department that provide both 'indirect' and 'direct' services to other cost types like 'housekeeping'.
Then, at level 2, you would disburse only the 'overheads' cost type, from all the 'indirect' departments, and all the departments that
provide both 'indirect' and 'direct' services. You would use the same 'attributes' for this second disbursement, but the outcomes would be
different as progressively, there would be less departments available for disbursement. The first department to disburse it's 'overhead' costs,
based upon 'total' expenditure, would disburse that cost to all the other departments, excluding itself. The second department to disburse
it's 'overhead' costs, based upon 'total' expenditure, would disburse it's 'overhead' costs to all other departments, excluding the itself
and the first department. Eventually, the second last department would have only one other 'indirect' department to which it could disburse it's 'overhead',
plus all the 'direct' patient care departments. The last department would have only the 'direct' patient care departments to which it could
disburse it's 'overhead' costs. As a result, with the 'Cascade' strategy, and proportional disbursement, the proportions change during the disbursal process.

An alternate strategy, called 'Iteration', allows all costs to be disbursed according to the 'attributes' and leverage the fact that most 'indirect' costs
will go to 'direct' patient care departments. Which means that the amount of costs disbursed from 'indirect' departments
back to 'indirect' departments will be small.  And those residual costs can be disbursed, based upon the very same 'attributes',
resulting in even less costs being disbursed from 'indirect' departments back to 'indirect' departments.
This process can be repeated as many times as it takes, until the cost held in the 'indirect' departments is deemed to be
so small as to be insignificant.

All of this disbursing of 'indirect' costs is configured as part of the clinical costing model. The rest of the clinical costing model
deals with the distribution of all costs to Clinical Events. But first the clinical events need to be built from the Patient Activity data.
How those clinical events are built and how costs are distributed to them is the rest of the clinical costing model, which has to be
loaded at this stage.

##### Direct Cost Modelling
Clinical costing events are snippets of Patient Activity data, for specific patients, with specific characteristics, that can be associated
with specific activities associated with a department or part of a department. That selection is done using an SQL 'where' clause,
such as 'where the patient attenced a specific clinic' or 'where the patient was addmitted under a specific clinical specialty' or
'where the patient attended theatre and the surgeon was a specific surgeon'. The selection 'where' clause will often have some
relationship to a general ledger account that has been shaped, ready for distribution.

Clinical costing events have 'weights' so that costs are not distributed evenly across them,
but rather more costs are allocated to Patient Activities that consume more costs.
Those 'weights' start with attributes of the Patient Activity data such 'minutes in theatre' or 'minutes under anasthesia'
or 'minutes being seen by a clinician in a clinic'. For inpatients there will be 'bed days' with a qualifier to distriguish
between '1 overnight bed day' and '1 same day bed day' as those two classes of Patient Activities may be costed diferently.
As an example, 'physioTherapy' clincal costing events would be chosen from just those patients who attended a 'Physiotherapy' clinic with
a 'weight' of 'attendance minutes'. The cost of running the Physiotherapy department would then be distributed over the 'physioTherapy' clinical
costing events, based up 'attendance minutes', resulting in more difficult, time consuming 'physioTherapy' clinical costing events receiving more costs.
Those 'physioTherapy' clinical costing events could then be linked back to the original Patient Activity and other related patient data
such as the patient's condition, thus, making it possible to determine which patient conditions were more expensive to treat.

Patient Activity data can include an 'acuity' measure. If the hospital has a patient and nurse dependancy application then
there would be a nursing 'acuity' associated with each patient bed day. The inpatient Patient Activity extract would
then have 'bed days' with an average 'acuity'. Nursing costs for each ward would then be distributed over 'bed days' in each ward
adjusted for 'acuity' of those 'bed days'. Thus, patient requiring more nursing care would attract more costs. However, for some
costs, adjusting for 'acuity' makes no sense. Cleaning costs would be distributed according to 'bed days' with no adjustment
for 'acuity'. When configuring a clinical costing event a 'where' clause must be specified, and an 'acuity scaling' factor (normally 1.0
where 'acuity' is available and applicable and 0.0 for all other clinical costing events).

Sometimes, but rarely, the 'weight' needs to be weighted for specific subsets of a clinical costing event.
For instance, the Kitchen purchase 'food' that gets turned into meals which are fed to patients. This could be treated as
an 'overhead' cost or you could treat it as a 'direct' cost. To treat it as a 'direct' cost you need to identify which patients
got fed. Now there may be a Kitchen application that could provide a 'feeder' identifying which patients got fed which meals at which cost.
Or you could assume that every inpatient who had a 'bed day' got fed. However, in this instance, not all 'bed days' are the same.
For most wards a patient gets three meals and a cup of tea every day, but in the Limited Care Dialysis Unit they patients only
get a light meal of sandwiches. To cater for this two 'food' clinical costing events would be configured.
The first would be 'where' bed days were not 'same_day' bed days, with 'weight' for bed days of 3.30.
The second would be 'where' a same day bed day was admitted to the Limited Care Dialysis Unit with a 'weight' for that bed day of 1.00.
All the Kitchen 'food' costs would then be distributed across all these 'food' clinical costing events based upon these 'weighted bed days'.

Having configured all the general ledger grouping and shaping, and all the clinical costing events, all the remains is to configure
how those shaped general ledger accounts are going to be distributed over those clinical costing events.
Sometimes a shaped general ledger account may need to be distributed over more than one class of clinical costing event.
For example the surgical medical officer may do ward rounds and write discharge summaries. This shaped general ledger cost
needs to be distributed over 'surgical bed days' and 'surgical patients discharged during the clinical costing period';
two different classes of clinical costing events. To facilitate this this each distribution is configured with
a  'distribution fraction'. For the surgical medical officer there would be two distributions, one over 'surgical bed days' and
the other over 'surgical patients discharged during the clinical costing period', each with different 'distribution fractions', where
the two 'distribution fractions' add up to 1.00. The assignement of those fractions would be based upon an estimate of
the proportion of time the surgical medical officer spent on these two tasks.

## The "Repeated" processes (once per clinical costing period).

### Loading the Hospital Activities workbook

#### ::: load_hospital_activity

The 'load_hospital_activity.py' script load the specified hospital activities workbook for the specified clinical costing period.
The hospital activities is a workbook of extracts from various patient administration systems of patient activity during the clinical costing period.
For inpatients this typically includes patients in hospital during the clinical costing period with associated factors (dimensions) that
can be used for selecting subsets and quantities (measures) that can be used for clinical costing event weights.
Factors (dimensions) might include 'clinical specialty', 'admitting ward', 'admitting doctor' and 'discharge ward'.
Quantities (measures) might include 'bed days', 'bed hours', 'same day' and 'bed transfers during the clinical costing period'.
Usually there will be additional factors (dimensions) which will be used for reporting the clinical costs, such as 'DRG', 'care type',
'patient category', 'patient financial category', 'sex', 'ethnicity' and 'postcode'.
Some things like 'patients admitted during the clinical costing period' and 'patients discharged during the clinical costing period' will
need their own extract (worksheet). Because patient get transfered during episode of care, there will also be an additional extract
of 'ward days' and 'ward hours' by ward. Similarly patients sometimes go to Theatre during episodes of care, sometime more than once.
So, there will be a Patient Activity extract of Theatre attendances with associated factors (dimensions) and quantities (measures).

There will be similar extracts for outpatient Clinics and Accident/Emergency attendances.


### Loading the Hospital Costs workbook

#### ::: load_hospital_costs

The 'load_hospital_costs.py' script load the specified hospital costs workbook for the specified clinical costing period.
The hospital costs is a workbook of cost details for the clinical costing period.
The main worksheet will be the general ledger extract for the clinical costing period.
There will also be worksheets for each 'feeder' or 'itemized costs' extract.
There will also be a worksheet of 'run adjustments' being known/idenified costs that need to taken out of a more general ledger account
so that they can be costed independently of any processing for the more general ledger account.
For instance, payroll may provide a list of how much certain staff were paid during the clinical costing period and those same staff
can be associated with specific clinical costing events.
The final worksheet provides the ability to adjust general ledger account attributes.
For instance, a ward may close some beds during the clinical costing period which means that this ward has less 'floor space' to clean
during this clinical costing period. Hence an adjustment for the 'floor space' for this ward is required,
but just for this clinical costing period.

### Build the Hospital Costs

#### ::: build_costs

The 'build_costs.py' script applies the general ledger mapping, grouping and shaping as configured in the specified clinical costing model,
to the hospital costs for the specified hospital, for the specified clinical costing period.
The 'build_costs.py' script report the total expenditure for the clinical costing period after each stage of mapping, grouping and shaping.
These figures should be identical and any descripancy is an indication of an error in the configuration of the clinical costing model
and must be investigated and corrected before proceeding.
The clinical costing model can be edited and re-loaded, and the costs re-built, with some limitations on editing the clinical costing model.
Firstly you cannot delete codes as they may have been used in previous clinical costing runs.
However you can ensure that a code is not used in the re-defined clinical costing model.
And there is a database limitation that prevents you from changing the case of letters in a code.
If you need to delete a code, or change the case of a letter in a code then you have two choices.
Firstly you can change the code for the clinical costing model, thus creating a new clinical costing model.
Secondly, you can start an new database and load everything from scratch.
If you are working in a test environment then you have a third option of deleting all the tables in the database and starting from scratch.

### Disburse the Hospital Indirect Costs

#### ::: disburse_costs

The 'disburse_costs.py' script disburses all the 'indirect' costs for the specified hospital,
according in the configuration in the specified clinical costing model, for the specified clinical costing period.
An option is provided that select either the 'Cascade' or 'Iteration' disbursement method.
The 'disburse_costs.py' script reports the amount of 'indirect' costs before and after disbursement.
If the 'indirect' costs after disbursement is not zero, or close to zero, then there is error in the configuration
of the clinical costing model which must be investigated and corrected before proceeding.
The clinical costing model can be edited, re-loaded, the costs re-built and re-disbursed, with some limitations on editing the clinical costing model.
Firstly you cannot delete codes as they may have been used in previous clinical costing runs.
However you can ensure that a code is not used in the re-defined clinical costing model.
And there is a database limitation that prevents you from changing the case of letters in a code.
If you need to delete a code, or change the case of a letter in a code then you have two choices.
Firstly you can change the code for the clinical costing model, thus creating a new clinical costing model.
Secondly, you can start an new database and load everything from scratch.
If you are working in a test environment then you have a third option of deleting all the tables in the database and starting from scratch.

### Build the Clinical Costing Events

#### ::: build_events

The 'build_events.py' script build all the clinical costing events as configured in the specified clinical costing model,
for the specified hospital, for the specified clinical costing period.

### Distribute all Costs

#### ::: distribute_costs

The 'distribute_costs.py' script distributes all the costs for the specified hospital,
according in the configuration in the specified clinical costing model, for the specified clinical costing period.
The 'distribute_costs.py' script reports the total costs to be distributed and total costs actually distributed.
Any discrepency should be noted and explained in any clinical costing report. Normally these will be period differences
with costs from other clinical costing periods being included in the general ledger extract and specifically excluded
by the clinical costing model. Sometimes the clinical costing process is the only way of identifying and excluding
these types of general ledger costs; things included in the general ledger to satisfy accounting standards,
but not relevant to the computation of clinical costs.

## The Reporting Processes
The **Clincial Costing System** does not include a reporting solution. Ideally, given the nature of clinical costs,
reports would be created using something like Tableau or Microsoft Power BI.
Views over the data may help this process.
The 'tools/createSQLAlchemyDBview.py' script gives an example of how views on the database can be created using Python
and SQLAlchemy.
### ::: createSQLAlchemyDBviews

