# CADOR project (Application Case: Decision, Optimization and Responsibility)

Hospital staff scheduling

## Planning data csv file format

The planning data is stored in a csv file with the following special format:

    instance_id                     <id>
    year                            <yyyy>
    budgeted_workforce              <bw>
    annual_hours_fix                Tdf Tnf
    annual_hours_var                Tdv Tnv
    partial_time_contracts_prop     <Pp>
    eighty_percent_contracts_prop   <P80>
    contracts_type                  1   2   3   4   5   6   7
    contracts_ratios                1   .9  .8  .75 .7  .6  .5
    contracts_costs                 1   .91 .85 .75 .7  .6  .5
    contracts_availability          A_1 A_2 A_3 A_4 A_5 A_6 A_7
    contracts_affected              a_1 a_2 a_3 a_4 a_5 a_6 a_7
    day_shifts                      M   J   S   ...
    night_shifts                    N   ...
    week_days                       L   Ma  Me  J   V   S   D
    week_indices                    0   1   2   3   4   5   6
    s                               Ns0 Ns1 Ns2 Ns3 Ns4 Ns5 Ns6     ts  cs  Ds  <bDs>
    s'                              Ns'0    ...     ...     Ns'6    ts' cs' Ds' <bDs'>
    s''                             Ns''0   ...     ...     Ns''6   ts''    ...
    ...                             ...                     ...     ...
    sn                              Nsn0    ...      ...    Nsn6    tsn     ...

Notes: 
- *T*[*k*,*q*] : number of annual working hours for workforce in *q* rest in *k* shifts (*q = f* or *v* for fixed or 
variable and *k = d* or *n* for day or night)
- *N*[*s*,*j*] : the need of health employees for the shift *s* at the day *j* of a week
- *t*[*s*] : the beginning time of the shift *s*
- *c*[*s*] : the completion time of the shift *s*
- *D*[*s*] : the duration of the shift *s*
- *bD*[*s*] : the break duration in the shift *s*

The name of the planning data file is, by convention : "planning_data_file_<*id*>.csv"
