#%% [markdown]
# # PROPERTY PROFORMA CREATION
# ---
# This notebook can be used to create a proforma spreadsheet for any Real Estate investment. 
# 
# When finished this notebook will contain structures for:
#    1. Creating Rent Rolls from Individual Leases
#    2. Calculating financing costs and an amortization schedule for properties
#    3. Estimating construction costs for new projects, and evaluating construction time and financing scenarios
#    4. Comparing multiple purcahse price scenarios
#    5. Estimating future income and expenses for properties
#    6. Comparing multiple projects and properties shit

#%%
import pandas as pd
from datetime import date
import numpy as np
from collections import OrderedDict, namedtuple
from dateutil.relativedelta import *
from dateutil.rrule import rrule, MONTHLY
from pandas.tseries.offsets import MonthEnd
import xlsxwriter

#%% [markdown]
# # Income Functions
# ---
# ## Creating a Lease Object
# 
# The below function takes the inputs of a single tenant's lease. It returns a tuple with two seperate DataFrames.
# 
# **Inputs necissary to create a Lease Object are:**
#    1. Lease Start Date
#    2. Lease End Date
#    3. Tenant's Name
#    4. Suite Number
#    5. Rental Rate PSF
#    6. Occupied SF
#    7. Expense Reimbursement Type
#    
# **The function will output a tuple with two DataFrames that can be accessed at:**
# * **_newLease.schedule_**
#     * This provides a table with complete month by month rent calculations and accounts for partial month leases
# * **_newLease.stats_**
#     * This provides general statistics about the tenant's lease including:
#         1. Tenant Name	
#         2. Suite	
#         3. Rental Rate	
#         4. SF Occupied
#         5. Total Lease Value	
#         6. Start Date	
#         7. End Date	
#         8. Number of Months	
#         9. Expense Type
# 
# Once a Lease Object is created it can be input into a Rent Roll Object along with other leases. 

#%%
def newLease(start_date,end_date,tenant_name,suite,rental_rate_psf,occupied_sf,expense_type):
    
    #need to find the end of the last month or it wont be included, all index values use the last day of the month
    end_date_month = pd.to_datetime(end_date) + MonthEnd(0) 
    
    #create the index date range for this particular lease
    month_array = pd.date_range(start = start_date, end = end_date_month, freq="M")
    
    #actual_start_date =  start_date - datetime.timedelta(days=1)
    #actual_end_date =  end_date + datetime.timedelta(days=1)
    
    #setup the schedule DataFrame
    schedule = pd.DataFrame({'tenantName': tenant_name, 
                             'suite': suite,
                             'occupiedSF': occupied_sf,
                             'rentalRate': rental_rate_psf,                        
                            },
                            index = month_array)
    
    schedule['fullMonthRent'] = (schedule['occupiedSF'] * schedule['rentalRate']) / 12
    #need to round all partial cents up
    schedule['fullMonthRent'] = (np.ceil(schedule['fullMonthRent'] * 100))/100


    #these check the month and year of the index to see if they are the first or last month to account for partial month leases
    schedule['isFirstMonth'] = (pd.to_datetime(schedule.index).month == pd.to_datetime(start_date).month) & (pd.to_datetime(schedule.index).year == pd.to_datetime(start_date).year)
    schedule['isLastMonth'] = (pd.to_datetime(schedule.index).month == pd.to_datetime(end_date).month) & (pd.to_datetime(schedule.index).year == pd.to_datetime(end_date).year)

    #then we count how many days are in the partial month
    schedule['firstMoDays'] = np.where(schedule['isFirstMonth']==True, (pd.to_datetime(schedule.index).day - pd.to_datetime(start_date).day + 1), 0)
    schedule['lastMoDays'] = np.where(schedule['isLastMonth']==True, pd.to_datetime(end_date).day, 0)

    schedule['partialDays'] = schedule['firstMoDays'] + schedule['lastMoDays']

    #calculates the rent for a partial month lease
    schedule['collectedRent'] = (schedule['fullMonthRent'] / pd.to_datetime(schedule.index).day) * schedule['partialDays']
    
    
    #puts the full month rent amount into the schedule of collected rent
    
    
    schedule['collectedRent'] = schedule['collectedRent'].replace(0.0, schedule['fullMonthRent'])
    schedule['expenseType'] = expense_type
    schedule['startYear'] = pd.to_datetime(start_date).year
    
    schedule = schedule.round(2)
    
    #create stats for use outside of rent schedule
    
    months_in_lease = int(np.around((pd.to_datetime(end_date) - pd.to_datetime(start_date))/np.timedelta64(1, 'M')))
    
    stats = pd.Series([start_date, 
                       end_date, 
                       tenant_name, 
                       suite,
                       rental_rate_psf,
                       occupied_sf,
                       schedule["collectedRent"].sum(), 
                       months_in_lease, 
                       expense_type],
                       index=["Start Date", "End Date", "Tenant Name", "Suite", "Rental Rate", "SF Occupied","Total Lease Value", 
                             "Number of Months", "Expense Type"])
    
    #creates a named tuple so the two data frames can be accessed easily
    
    Lease = namedtuple("Lease", ["schedule", "stats"])
    lease = Lease(schedule, stats)    
    
    return lease

#%% [markdown]
# ### Example: Creating New Leases
# The below code creates 3 new lease objects that will be used throughout the rest of the notebook.

#%%
#exampes of creating a new lease
lease1 = newLease(start_date = date(2018,6,1), 
                    end_date = date(2030,5,31), 
                    tenant_name = "Cavendish Kinetics", 
                    suite = "100",
                    rental_rate_psf = 22.00,
                    occupied_sf = 3481.00,
                    expense_type = "BASE YEAR")

lease2 = newLease(start_date = date(2018,9,1), 
                    end_date = date(2030,8,31), 
                    tenant_name = "North Park Dental", 
                    suite = "103",
                    rental_rate_psf = 17.46,
                    occupied_sf = 1235.00,
                    expense_type = "NNN")

lease3 = newLease(start_date = date(2018,5,1), 
                    end_date = date(2030,6,30), 
                    tenant_name = "International Tutoring", 
                    suite = "201",
                    rental_rate_psf = 21.50,
                    occupied_sf = 2190.00,
                    expense_type = "NNN")

leaseArray = [lease1.schedule, lease2.schedule, lease3.schedule]

pd.DataFrame([lease1.stats, lease2.stats, lease3.stats])


#%%
lease2.schedule.to_csv('lease.csv')

#%% [markdown]
# ## Calculating Expenses and Reimbursments
# 
# Need to create a function the takes in a lease and a series of expenses to determine the correct amount of expenses a tenant pays each month. 
# 
# We will most likely only have one years expenses, so we will need to extrapolate forwards; but it would be nice to have the ability to input multi-years expenses.
# 
# Do we need the ability to extrapolate backwords for base year leases?

#%%
def newExpense(expense,amount,year,frequency=1,addTo=(pd.DataFrame())):
    new = pd.DataFrame.from_records([{"Expense": expense,"Amount": amount,"Frequency": frequency, "Yearly Expense":(amount*frequency), 'Year': year}])
    
    if addTo.empty:
        return new
    else:
        return addTo.append(new,ignore_index=True)


#%%
#If you dont pass it an addTo dataframe it will create one
expenses = newExpense("Tax", 2300, 2019)
#if you do it will addTo the existing dataframe
expenses = newExpense("Insurnce", 2300, 2019, addTo=expenses)
#another way to add new expenses
expenses = expenses.append(newExpense("Utilities", 2300, 2019, 12),ignore_index=True)

print(expenses)

expenseAmount = expenses['Yearly Expense'].sum()
expenseAmount

#%% [markdown]
# ## Creating a Rent Roll Object
# The below function takes an input of a Lease Array to combine multiple leases into one Rent Roll. 
# 
# It returns a tuple with 3 seperate DataFrames:
# * **_newRentRoll.full_**
#     * contains a month by month table of all tenants and the rent amounts they pay in a given month
# * **_newRentRoll.monthly_**
#     * Summarizes the full table into a total monthly income from the individual leases
# * **_newRentRoll.yearly_**
#     * Summarizes the data into a full years income from all leases

#%%
#now we need to make a DataFrame similar to the one in newLease, that holds all the seperate leases with months as index

def newRentRoll(leaseArray):
    propertyRentSchedule = pd.DataFrame()

    for lease in leaseArray:
        propertyRentSchedule = pd.concat([propertyRentSchedule, lease])

    propertyRentSchedule.sort_index(inplace=True)
    #propertyRentSchedule.to_csv('propertyRentSchedule.csv')

    ####
    monthlyRentSchedule = pd.DataFrame()
    monthlyRentSchedule['monthsRent'] = propertyRentSchedule.groupby(propertyRentSchedule.index)['collectedRent'].sum()
    monthlyRentSchedule['leaseCount'] = propertyRentSchedule.index.value_counts()
    monthlyRentSchedule['year'] = pd.to_datetime(monthlyRentSchedule.index).year

    #monthlyRentSchedule.to_csv('monthlyRentSchedule.csv')

    monthlyRentSchedule.head()

    ####
    yearlyRentSchedule = pd.DataFrame()
    yearlyRentSchedule['yearsRent'] = monthlyRentSchedule.groupby(monthlyRentSchedule['year'])['monthsRent'].sum()
    yearlyRentSchedule
    
    #creates a named tuple so the three versions can be accessed easily
    
    RentRoll = namedtuple("RentRoll", ["full", "monthly", "yearly"])
    rentRoll = RentRoll(propertyRentSchedule, monthlyRentSchedule, yearlyRentSchedule)                              
                                      
    return rentRoll

#%% [markdown]
# ### Example: Creating a New Rent Roll Object
# The below code creates a rent roll from the 3 new lease objects created in the previous section. Examples of the full, monthly, and yearly DataFrames are shown.

#%%
sampleRentRoll = newRentRoll(leaseArray)

sampleRentRoll.full.head()


#%%
test = sampleRentRoll.full
expenses = 40012.89
building_size = 2190 + 3481 + 1235
percent_increase = 0.03

hmm = (test.occupiedSF / building_size) * (expenses - np.fv(percent_increase, test.startYear - test.index.year, 0, -1*expenses))

test['prorataShare'] = (test.occupiedSF / building_size) * 100

#change the expenses on NNN to be the FV of the expenses so it changes from year to year
test['expenseAmount'] = pd.np.where(test.expenseType.str.contains("NNN"), (test.occupiedSF / building_size) * expenses,
                        pd.np.where(test.expenseType.str.contains("BASE YEAR"),((test.occupiedSF / building_size) * (expenses - np.fv(percent_increase, test.startYear - test.index.year, 0, -1*expenses))/12), "na"))
test.round(2)


#%%
sampleRentRoll.monthly.head()


#%%
sampleRentRoll.yearly


#%%
# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter('rentroll_multiple.xlsx', engine='xlsxwriter')

# Write each dataframe to a different worksheet.
sampleRentRoll.full.to_excel(writer, sheet_name='Full Rent Roll')
sampleRentRoll.monthly.to_excel(writer, sheet_name='Monthly Rent Roll')
sampleRentRoll.yearly.to_excel(writer, sheet_name='Yearly Rent Roll')
test.to_excel(writer, sheet_name='expenses')

# Close the Pandas Excel writer and output the Excel file.
writer.save()

#%% [markdown]
# # Expenses
# ---
# 
# ## Creating an Amortization Schedule
# 
# Creating an amortization schedule is done by calling the *amortization_table* function. This function calls on the *amortize* function to iterate through each period of the loan to calculate begining and ending balances. This is necissary to account for additional payment in excess of the required payment. Additional payments decrease the prinicpal of the loan and the interest needs to be recalculated when  
# 
# To create an amortization schedule call the *amortization_table* function using the parameters:
# 
# * **principal**: Amount borrowed
# * **interest_rate**: The annual interest rate for this loan
# * **years**: Number of years for the loan
#     
# * **annual_payments** (optional): Number of payments in a year. DEfault 12.
# * **addl_principal** (optional): Additional payments to be made each period. Default 0.
# * **start_date** (optional): Start date. Default first of next month if none provided
# 
# *amortization_table* returns a tuple with two DataFrames: 
# * **schedule**: Amortization schedule as a pandas dataframe
# * **summary**: Pandas dataframe that summarizes the payoff information
# 
# *amortization_table* passes the variables into *amortize* to iterate through and recalculate interest after additional payments have been made above the required payment.
# 
# *amortize* requires these parameters:
# 
# * **principal**: Amount borrowed
# * **interest_rate**: The annual interest rate for this loan
# * **years**: Number of years for the loan
# * **pmt**: Payment amount per period
# * **addl_principal**: Additional payments to be made each period.
# * **start_date**: Start date for the loan.
# * **annual_payments**: Number of payments in a year.
# 
# *amortize* returns:
# * **schedule**: Amortization schedule as an Ordered Dictionary
# 

#%%
def amortize(principal, interest_rate, years, pmt, addl_principal, start_date, annual_payments):

    # initialize the variables to keep track of the periods and running balances
    p = 1
    beg_balance = principal
    end_balance = principal
    
    while end_balance > 0:
        
        # Recalculate the interest based on the current balance
        interest = round(((interest_rate/annual_payments) * beg_balance), 2)
        
        # Determine payment based on whether or not this period will pay off the loan
        pmt = min(pmt, beg_balance + interest)
        principal = pmt - interest
        
        # Ensure additional payment gets adjusted if the loan is being paid off
        addl_principal = min(addl_principal, beg_balance - principal)
        end_balance = beg_balance - (principal + addl_principal)

        yield OrderedDict([('Month',start_date),
                           ('Period', p),
                           ('Begin Balance', beg_balance),
                           ('Payment', pmt),
                           ('Principal', principal),
                           ('Interest', interest),
                           ('Additional_Payment', addl_principal),
                           ('End Balance', end_balance)])
        
        # Increment the counter, balance and date
        p += 1
        start_date += relativedelta(months=1)
        beg_balance = end_balance


#%%
def amortization_table(principal, interest_rate, years,
                       addl_principal=0, annual_payments=12, start_date=date.today()):

    # Payment stays constant based on the original terms of the loan
    payment = -round(np.pmt(interest_rate/annual_payments, years*annual_payments, principal), 2)
    
    # Generate the schedule and order the resulting columns for convenience
    schedule = pd.DataFrame(amortize(principal, interest_rate, years, payment,
                                     addl_principal, start_date, annual_payments))
    schedule = schedule[["Period", "Month", "Begin Balance", "Payment", "Interest", 
                         "Principal", "Additional_Payment", "End Balance"]]
    
    # Convert to a datetime object to make subsequent calcs easier
    schedule["Month"] = pd.to_datetime(schedule["Month"])
    
    #Create a summary statistics table
    payoff_date = schedule["Month"].iloc[-1]
    stats = pd.Series([payoff_date, schedule["Period"].count(), interest_rate,
                       years, principal, payment, addl_principal,
                       schedule["Interest"].sum()],
                       index=["Payoff Date", "Num Payments", "Interest Rate", "Years", "Principal",
                             "Payment", "Additional Payment", "Total Interest"])
    
    #creates a named tuple so the three versions can be accessed easily
    
    AmortizationTable = namedtuple("AmortizationTable", ["schedule", "stats"])
    amortizationTable = AmortizationTable(schedule, stats)                              
                                      
    return amortizationTable

#%% [markdown]
# ### Example: Creating an Amortization Schedule

#%%
amort1 = amortization_table(700000, .04, 30, addl_principal=200, start_date=date(2016, 1,1))
amort2 = amortization_table(100000, .04, 30, addl_principal=50, start_date=date(2016,1,1))
amort3 = amortization_table(100000, .05, 30, addl_principal=200, start_date=date(2016,1,1))
amort4 = amortization_table(100000, .04, 15, addl_principal=0, start_date=date(2016,1,1))

pd.DataFrame([amort1.stats, amort2.stats, amort3.stats, amort4.stats])


#%%
amort4.schedule.head()


