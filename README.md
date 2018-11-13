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
    * most finance arent that complicated

5. construction costs
    * create an expense table like for expenses.
    * create a bell curve model for estimating construction financing
    * maybe build a table of Retail, Industrial, MF construction cost ranges
    * include hard and soft costs

6. pro forma output 
    * just set up a seperate file that holds all variables and create a function that turns it into a spreadsheet, figure out the best way to show a scenario on a single sheet. May need two seperate templates for construction/non construction
    * maybe just do this in a notebook? then a spreadsheet? then figure out how to assemble into an HTML layout

7. re-tenanting
    * look at table, when a lease ends account for retenant period, then increase rent and start a new lease
    * add to table and return the table

8. lease return tuple?
    * should lease objects and rent roll objects return a tuple?
    * might make more sense to remove the stats and different rent roll versions to clean up code and Make seperate functions that return similar summarized tables

8. Make seperate CLI apps to run through a proforma and output a spreadsheet. Will need one for Existing Buildings and one for Construction Projects.

9. Once the flow is completed it should be easier to move to A Web based version