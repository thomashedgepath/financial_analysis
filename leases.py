import pandas as pd
import datetime as dt
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
lease1 = newLease(start_date = dt.date(2018,6,1),
                    end_date = dt.date(2030,5,31),
                    tenant_name = "Cavendish Kinetics",
                    suite = "100",
                    rental_rate_psf = 22.00,
                    occupied_sf = 3481.00,
                    expense_type = "BASE YEAR")

lease2 = newLease(start_date = dt.date(2018,9,1),
                    end_date = dt.date(2030,8,31),
                    tenant_name = "North Park Dental",
                    suite = "103",
                    rental_rate_psf = 17.46,
                    occupied_sf = 1235.00,
                    expense_type = "NNN")

lease3 = newLease(start_date = dt.date(2018,5,1),
                    end_date = dt.date(2030,6,30),
                    tenant_name = "International Tutoring",
                    suite = "201",
                    rental_rate_psf = 21.50,
                    occupied_sf = 2190.00,
                    expense_type = "NNN")

leaseArray = [lease1.schedule, lease2.schedule, lease3.schedule]

print(pd.DataFrame([lease1.stats, lease2.stats, lease3.stats]))
