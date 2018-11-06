import pandas as pd
import datetime
import numpy as np
import collections
from dateutil.relativedelta import *
from dateutil.rrule import rrule, MONTHLY
from pandas.tseries.offsets import MonthEnd
import xlsxwriter

def newLease(start_date,end_date,tenant_name,suite,rental_rate_psf,occupied_sf,expense_type):
    
    #need to find the end of the last month or it wont be included, all index values use the last day of the month
    end_date_month = pd.to_datetime(end_date) + MonthEnd(0) 
    
    #create the index date range for this particular lease
    month_array = pd.date_range(start = start_date, end = end_date_month, freq="M")
    
    actual_start_date =  start_date - datetime.timedelta(days=1)
    actual_end_date =  end_date + datetime.timedelta(days=1)
    
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
    
    Lease = collections.namedtuple("Lease", ["schedule", "stats"])
    lease = Lease(schedule, stats)    
    
    return lease

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

def newExpense(expense,amount,year,frequency=1,addTo=(pd.DataFrame())):
    new = pd.DataFrame.from_records([{"Expense": expense,"Amount": amount,"Frequency": frequency, "Yearly Expense":(amount*frequency), 'Year': year}])
    
    if addTo.empty:
        return new
    else:
        return addTo.append(new,ignore_index=True)

    
#If you dont pass it an addTo dataframe it will create one
expenses = newExpense("Tax", 2300, 2019)
#if you do it will addTo the existing dataframe
expenses = newExpense("Insurnce", 2300, 2019, addTo=expenses)
#another way to add new expenses
expenses = expenses.append(newExpense("Utilities", 2300, 2019, 12),ignore_index=True)

print(expenses)

expenseAmount = expenses['Yearly Expense'].sum()
expenseAmount

expenseAmount = expenses['Yearly Expense'].sum()

def calculateLeaseExpenses(lease,building_size,expenses,year,percent_increase=0.03):
    
    prorata_share = lease.stats['SF Occupied'] / building_size
    
    #if statement to determine how expenses are calculated based on type
    if lease.stats['Expense Type'] == 'NNN':
        return prorata_share * expenses             
    elif lease.stats['Expense Type'] == 'BASE YEAR':
        base_year = lease.stats['Start Date'].year
        if base_year == year:
            return 0   
        else:
            num = base_year - year
            base_year_expenses = np.fv(percent_increase, num, 0, -1*expenses)
            val = (expenses - base_year_expenses) * prorata_share
            return val
    elif lease.stats['Expense Type'] == 'FULL SERVICE':
        return 0
    elif lease.stats['Expense Type'] == 'PLUS UTILITIES':
        return 0
    else:
        print("Invalid expense type for lease")

calculateLeaseExpenses(lease1,6906,expenseAmount,2019)

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
    
    RentRoll = collections.namedtuple("RentRoll", ["full", "monthly", "yearly"])
    rentRoll = RentRoll(propertyRentSchedule, monthlyRentSchedule, yearlyRentSchedule)                              
                                      
    return rentRoll

sampleRentRoll = newRentRoll(leaseArray)

sampleRentRoll.full.head()

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter('rentroll_multiple.xlsx', engine='xlsxwriter')

# Write each dataframe to a different worksheet.
sampleRentRoll.full.to_excel(writer, sheet_name='Full Rent Roll')
sampleRentRoll.monthly.to_excel(writer, sheet_name='Monthly Rent Roll')
sampleRentRoll.yearly.to_excel(writer, sheet_name='Yearly Rent Roll')

# Close the Pandas Excel writer and output the Excel file.
writer.save()

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
    
    AmortizationTable = collections.namedtuple("AmortizationTable", ["schedule", "stats"])
    amortizationTable = AmortizationTable(schedule, stats)                              
                                      
    return amortizationTable

amort1 = amortization_table(700000, .04, 30, addl_principal=200, start_date=date(2016, 1,1))
amort2 = amortization_table(100000, .04, 30, addl_principal=50, start_date=date(2016,1,1))
amort3 = amortization_table(100000, .05, 30, addl_principal=200, start_date=date(2016,1,1))
amort4 = amortization_table(100000, .04, 15, addl_principal=0, start_date=date(2016,1,1))

pd.DataFrame([amort1.stats, amort2.stats, amort3.stats, amort4.stats])