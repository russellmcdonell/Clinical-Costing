# Welcome to Clincal Costing
A system for allocating costs to records of patient care.

## Outline
Clinical Costing is the process of allocating costs, from the General Ledger, for a specific period, to records of patient care, for the matching period.
Ideally this is done by following every patient, for every second of their episode of care, and recording everything that happened and the associated direct and indirect costs.
Obviously that's impractical, but a good approximation can be achieved by an algorithmic distribution of costs recorded in the General Ledger.
And, surprisingly, this can be done with one simple algorithm; proportional distribution.
The art in clinical costing, and it is an art, is in configuring funding source and target, and then determining the bases for the computation of the proportions used for the proportional distribution.
The 'weights' can be anything, in any unit of measure.
For medicines you could use the cost of the drug, over the counter a the local pharmacist, plus any goverment subsidy for the drug, as the weight; the market price.
That "weight" would be a dollar value, but the sum of these weights would not be the same as the cost of running the pharmacy.
None the less, you could proportionally distribute the cost of running the pharmacy to patients, based upon these "weights" for the drugs administered to each patient.

However, one pharmacist may spend all day, every day, doing rounds and checking the drug charts of every patient.
You could take this salary, and the associated overheads, out of the cost of running the pharmacy and distribute it independently to patients based upon bed days (a weight of 1.0 for each bed day).
You can even scale this "bed day", for each patient, by the count of drugs administed to the patient each day, on the assumption that more drugs means a longer drug chart and more to check.

As you can see, the art of clinical costing is the art of making assumptions about what things reflect, or are a proxy for, actual costs.
For instance, you could distribute "Power" based upon floor space but this ignores the fact that some departments, such as Radiology, use specific pieces of equipment, that consume considerable amounts of power.
So the "weights" for "Power" might be floor space multiplied by a scaling factor for each area.

## Indirect and Direct Costs
Clinical Costs can envisaged as two different types of costs; direct and indirect.
The lines here can get a little blurred.
For instance a pathology test involves a direct cost and "Payroll Services" are definitely an indirect cost.
Nurses wages would seem to be a direct cost, but without a Patient and Nurse Dependency Application you have no way of knowing which nurse spent how much time with each patient.
And nurses have non-patient-contact time, such as filling in timesheets, checking stock and re-ordering.
So any direct allocation of nurses wages to patients will be an approximation.

Indirect costs are associated with indirect cost centres and can be proportionally distributed to direct cost centres and other indirect cost centres.
For instance, "Payroll Services" may be distributed to "Maintenance Department", and other cost centres, based upon total wages for the period.
And "Maintenance Department" may be distributed to other cost centres, such a "Medical Ward", "Emergency" and "Administration", based upon floor space.
"Administration" is another Indirect Cost centre that will need to be proportionaltly distributed.
To do this you need a solution that support a large number of levels of cascading costing.
However, some configurations could have costs cascading up, as well as down.
For instance, "Payroll Services" have offices (floor space), so some of their costs, distributed to "Maintenance Department" will come back when "Maintenance Department" is distributed on floor space.
To facilitate this, all Indirect Costs are distributed before any Direct Costs and there are two ways of doing that; cascading and iteration.
With a cascading distribution, Indirect Cost centres and ranked from most indirect to least indirect and costs are proportionally distributed from the Indirect Cost centres in that order,
with no costs being allowed to cascade back to an already distributed cost centre.
So, if "Payroll Services" is proportionally distributed before "Maintenance Department" and "Maintenance Department" is distributed on floor space, then "Payroll Services" is deemed to have no floor space,
thus preventing any costs returning to "Payrole Services".
With an iteration distribution there is no ranking and costs can flow from anywhere to anywhere.
After the first distribution most of the costs will have gone from Indirect Cost centres to Direct Cost centres, but some will have gone from an Indirect Cost centre to another Indirect Cost centre.
When this occurs another iteration of distribution will occur which will result in a reduction in the cost remaining in the Indirect Cost centres.
Futher iterations of distribution will be performed until the total cost remaining in all the Indirect Cost centres reaches an acceptable, small amount.
A cascading distrubution will be much faster that an interative distribution and an interative distribution may not result in a more accurate distribution of costs.
Fortunately, a single configuration can be distributed using either the cascading distrubution script or the iterative distribution script.

## Table of Contents

1. [How-To Guide](how-to-guide.md)
2. [The Process](theProcess.md)
3. [The Database design](theDatabase.md)
4. [The Functions](functions.md)

## System Overview

### Hospital Configuration
hospitalConfig is the starting point. The Clinical Costing system can store the clinical costs for multiple hospitals.
These are stored independantly. You don't need to set up another Clinical Costing system everytime you want to compute
the clinical costs at a different hospital. However the clinical costs at different hospitals
are not inherently comparable, because of the differences in how each hospital is run and managed.
For instance, the porter who moves patients to and from theatre may be part of a hospital wide portering service,
or may be a specific theatre staff member. Hence, in two different hospitals, theatre portering costs will be assigned
to patients from different cost centres in the general ledger. Similarly, one hospital may have an outsourced
pathology service that provides a phlebotomist who collect the blood samples, and in another hospital blood samples
may be collected by the nursing staff on the wards. Again, the phlebotomy costs associated with blood tests
will be computed differently.

Because each hospital is different, it is necessary to start the Clinical Costing process by defining
those things that are specific to each hospital, such as the departments (cost centres) and cost types (subjectives) in the general ledger,
plus the ward, clinics, theatres and the clinicians.
It is also necessary to define the events that take place in each hospital. Event are things that happen in the hospital, to which costs will
be attached. For instance, 'admission' and 'discharge' are events to which medical records costs will be assigned.
However, not every patient gets admitted and discharged during a specific clinical costing period.
If a month is being costed then some patients will have been admitted in the previous month and some patient
won't be discharge until the following month. Each event can be assigned costs from multiple sources.
A patient bed day may attract nursing costs, energy costs and administration overhead costs.

### Hospital Activity
Activities are the things that happen to patient, which in turn create events with associated weights.
A stay in a ward will create ward events with weights that reflect the duration of the stay.
Activity in the radiology department, associated with each patient, will create radiology events,
with weights that reflect the workload of the associated radiology activity. The cost of running the radiology
department will then be distributed to patients with radiology events, based upon the weights of those events.

### Hosptial Costs
Hospital costs are extracted from the general ledger. However, some direct patient costs are known.
For instance, prosthetics are purchased. If the hospital records prostetics against a patient episode, then exact cost is know from invoices.
Similarly, the hospital may outsource the Radiology service and may get an itemized bill each radiology examination.
If that invoice identifies the patient expisode, then that's another direct cost that is known.
These costs can be assigned directly to the relevant episode of care. However, these costs are already include in the general ledger extract.
One step in the clinical costing process is to assign these known direct costs to the matching episode of care,
and remove that amount from the general ledger.

## Acknowledgements
Staff at Preston and Northcote Community Hospital in Victoria, Australia, provided many of the insights and ideas for this work.

