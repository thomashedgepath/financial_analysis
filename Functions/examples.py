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

from leases import * 
from finance import *

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

#%% [markdown]
# ## Example: Creating New Leases
# The below code creates 3 new lease objects that will be used throughout the rest of the notebook.


lease1 = newLease(
 start_date = date(2018,9,1), 
 end_date = date(2030,8,31), 
 tenant_name = "North Park Dental", 
 suite = "103",
 rental_rate_psf = 17.46,
 occupied_sf = 1235.00,
 expense_type = "NNN")

lease2 = newLease(
 start_date = date(2018,5,1), 
 end_date = date(2030,6,30), 
 tenant_name = "International Tutoring", 
 suite = "201",
 rental_rate_psf = 21.50,
 occupied_sf = 2190.00,
 expense_type = "NNN")

#%% [markdown]
#A **_newLeaseSchedule_** can be used when a lease has yearly increases 
# (currently recalculates rent 1/1 of every year)

leaseSchedule = newLeaseSchedule(
 start_date = date(2018,6,15), 
 end_date = date(2030,5,12), 
 tenant_name = "Cavendish Kinetics",
 suite = "100",
 start_rental_rate_psf = 22.00,
 occupied_sf = 3481.00,
 expense_type = "BASE YEAR",
 percent_increase = 0.03)

leaseArray = [lease1.schedule, lease2.schedule, leaseSchedule.schedule]

pd.DataFrame([lease1.stats, lease2.stats, leaseSchedule.stats])

###Export Lease Schedule to csv (keep for reference)
leaseSchedule.schedule.to_csv('../Outputs/schedueleee.csv')


#%% [markdown]
# ### Example: Creating a New Rent Roll Object
# The below code creates a rent roll from the 2 newLease objects and 1 newLeaseSchedule object created in the previous section. Examples of the full, monthly, and yearly DataFrames are shown.

#%%
sampleRentRoll = newRentRoll(leaseArray)

sampleRentRoll.full.head()

#%% [markdown]
# # Expenses
# ---
# ## Tenant Expense Calculating
# First create an expense table by adding new expenses using **_newExpense_**
#%% 
#If you dont pass it an addTo dataframe it will create a new data frame with your expense
expenses = newExpense("Tax", 2300, 2019)
#if you do it will addTo the existing dataframe
expenses = newExpense("Insurnce", 2300, 2019, addTo=expenses)
expenseAmount = expenses['Yearly Expense'].sum()

#%% [markdown]
# Then you can calculate each tenants estimated expenses given a single years expenses using calculateExpenses
rent_roll_expenses = calculateExpenses(sampleRentRoll,expenseAmount,45000)
rent_roll_expenses.head()


#%% [markdown]
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


#%%
amort1 = amortization_table(700000, .04, 30, addl_principal=200, start_date=date(2016, 1,1))
amort2 = amortization_table(100000, .04, 30, addl_principal=50, start_date=date(2016,1,1))
amort3 = amortization_table(100000, .05, 30, addl_principal=200, start_date=date(2016,1,1))
amort4 = amortization_table(100000, .04, 15, addl_principal=0, start_date=date(2016,1,1))

pd.DataFrame([amort1.stats, amort2.stats, amort3.stats, amort4.stats])
