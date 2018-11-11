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

1. [done]refactor and clean code and seperate into leases, finance, proforma, examples

2. [done]finish the expense calculations methods

3. [done]create a method for rent schedules
    * Need to be able to extract newLease objects from the rent schedule
    * should take a rent_increase_pct 
    * also needs the ability to alter a year or months rent independently
    * should be able to output a rent schedule table like the one i made for bill (yearly_prosperity_rent.csv)
    * avoid rounding errors

4. expense functions:
    * commisions
    * irr
    * 

5. construction costs

6. pro forma output 
    * just set up a seperate file that holds all variables and create a function that turns it into a spreadsheet, figure out the best way to show a scenario on a single sheet. May need two seperate templates for construction/non construction
    * maybe just do this in a notebook? then a spreadsheet? then figure out how to assemble into an HTML layout

7. re-tenanting

8. 