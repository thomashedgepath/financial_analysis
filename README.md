# PROPERTY PROFORMA CREATION
---
This project can be used to create a proforma spreadsheet for any Real Estate investment. 

When finished this notebook will contain structures for:
   1. Creating Rent Rolls from Individual Leases
   2. Calculating financing costs and an amortization schedule for properties
   3. Estimating construction costs for new projects, and evaluating construction time and financing scenarios
   4. Comparing multiple purcahse price scenarios
   5. Estimating future income and expenses for properties
   6. Comparing multiple projects and properties


#To do:

1. refactor and clean code and seperate into leases, finance, proforma, examples

2. finish the expense calculations methods

3. create a method for rent schedules
    * Need to be able to extract newLease objects from the rent schedule
    * should take a rent_increase_pct 
    * also needs the ability to alter a year or months rent independently
    * should be able to output a rent schedule table like the one i made for bill (yearly_prosperity_rent.csv)
    * avoid rounding errors

4. 