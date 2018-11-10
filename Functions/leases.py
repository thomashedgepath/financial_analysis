#%%
import pandas as pd
from datetime import date
import numpy as np
from collections import OrderedDict, namedtuple
from dateutil.relativedelta import *
from dateutil.rrule import rrule, MONTHLY
from pandas.tseries.offsets import MonthEnd, YearEnd, DateOffset

#%%
#newLease is used for fixed variable leases, if there are rent increases you need to use newLeaseSchedule
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
#%%

#Rent Schedule for one tenant
#Use this to do % increases for the same tenant so you dont have to create a seperate lease item for every year
def newLeaseSchedule(start_date, end_date, tenant_name, suite, start_rental_rate_psf, occupied_sf, expense_type, percent_increase):
    #set variables
    first_year_end = pd.to_datetime(start_date) + YearEnd(0)
    end_year = pd.to_datetime(end_date) + YearEnd(0)

    i = end_year.year - first_year_end.year

    leaseArray = []
    rolling_start_date = start_date
    
    #run loop for each years lease, each lease is added to the Array
    for year in range(0,i):
        rolling_end_date = rolling_start_date + YearEnd(1)
        yearLease = newLease(rolling_start_date,rolling_end_date,tenant_name,suite,start_rental_rate_psf,occupied_sf,expense_type)
        start_rental_rate_psf = start_rental_rate_psf * (1 + percent_increase)
        rolling_start_date = rolling_end_date + DateOffset()
        leaseArray.append(yearLease)
    #need to add the final year seperately
    finalYear = newLease(rolling_start_date,end_date,tenant_name,suite,start_rental_rate_psf,occupied_sf,expense_type)
    leaseArray.append(finalYear)

    #combine all the years leases into one data frame
    tenantRentSchedule = pd.DataFrame()
    for lease in leaseArray:
        tenantRentSchedule = pd.concat([tenantRentSchedule, lease.schedule])

    tenantRentSchedule.sort_index(inplace=True)

    #overwrite the columns for firstMoRent, lastMoRent etc. - 

    tenantRentSchedule['isFirstMonth'] = (pd.to_datetime(tenantRentSchedule.index).month == pd.to_datetime(start_date).month) & (pd.to_datetime(tenantRentSchedule.index).year == pd.to_datetime(start_date).year)
    tenantRentSchedule['isLastMonth'] = (pd.to_datetime(tenantRentSchedule.index).month == pd.to_datetime(end_date).month) & (pd.to_datetime(tenantRentSchedule.index).year == pd.to_datetime(end_date).year)

    #then we count how many days are in the partial month
    tenantRentSchedule['firstMoDays'] = np.where(tenantRentSchedule['isFirstMonth']==True, (pd.to_datetime(tenantRentSchedule.index).day - pd.to_datetime(start_date).day + 1), 0)
    tenantRentSchedule['lastMoDays'] = np.where(tenantRentSchedule['isLastMonth']==True, pd.to_datetime(end_date).day, 0)

    tenantRentSchedule['partialDays'] = tenantRentSchedule['firstMoDays'] + tenantRentSchedule['lastMoDays']

    tenantRentSchedule['startYear'] = pd.to_datetime(start_date).year

    #set output to match the newLease output
    months_in_lease = int(np.around((pd.to_datetime(end_date) - pd.to_datetime(start_date))/np.timedelta64(1, 'M')))
    avg_rental_rate = ((tenantRentSchedule['fullMonthRent'].mean()/ occupied_sf)*12)

    stats = pd.Series([start_date, 
                       end_date, 
                       tenant_name, 
                       suite,
                       avg_rental_rate,
                       occupied_sf,
                       tenantRentSchedule["collectedRent"].sum(), 
                       months_in_lease, 
                       expense_type],
                       index=["Start Date", "End Date", "Tenant Name", "Suite", "Avg. Rental Rate", "SF Occupied","Total Lease Value", 
                             "Number of Months", "Expense Type"])
    
    #creates a named tuple so the two data frames can be accessed easily
    
    Lease = namedtuple("Lease", ["schedule", "stats"])
    lease = Lease(tenantRentSchedule, stats) 


    return lease

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

#%%
def newExpense(expense,amount,year,frequency=1,addTo=(pd.DataFrame())):
    new = pd.DataFrame.from_records([{"Expense": expense,"Amount": amount,"Frequency": frequency, "Yearly Expense":(amount*frequency), 'Year': year}])
    
    if addTo.empty:
        return new
    else:
        return addTo.append(new,ignore_index=True)


#%%
def calculateExpenses(rent_roll,expenses,building_size,percent_increase=0.03,expenses_year=2019):
 rent_roll = rent_roll.full

 rent_roll['prorataShare'] = (rent_roll.occupiedSF / building_size)
 #change the expenses on NNN to be the FV of the expenses so it changes from year to year
 rent_roll['expenseAmount'] = pd.np.where(rent_roll.expenseType.str.contains("NNN"), (rent_roll.occupiedSF / building_size) * np.fv(percent_increase, rent_roll.index.year - expenses_year, 0, -1*expenses),
 pd.np.where(rent_roll.expenseType.str.contains("BASE YEAR"),((rent_roll.occupiedSF / building_size) * (expenses - np.fv(percent_increase, rent_roll.startYear - rent_roll.index.year, 0, -1*expenses))/12), 0))

 rent_roll['expenseAmount'] = (np.ceil(rent_roll['expenseAmount'] * 100))/100

 return rent_roll
