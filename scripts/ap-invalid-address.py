''' 
GTG, J. Beasley
Data Quality Checks
AP - finds addresses with 
non-numeric values 
(letters, special characters, 
white space) '''


import arcpy
import os
from os import path
import datetime
from datetime import datetime
import logging
import sys
import time

arcpy.env.overwriteOutput = True

def print_to_stdout(a): 
      print(a)
      logging.info(a)
      sys.stdout.flush() 
      time.sleep(1)
      
def print_to_stderr(a):
      sys.stderr.write(a)
      logging.error(a)
      sys.stderr.flush()

def invalidAddress(ap):

    oid = 'AP_ID_GeoAdd'
    addnum = 'Add_Number'

    desc = arcpy.Describe(ap)
    out_fgdb = desc.path

    invalids = ''
    with arcpy.da.SearchCursor(ap, [oid, addnum]) as scur:
        for row in scur:
            if not str(row[1]).isdigit():
                invalids += "'{}', ".format(str(row[0]))
    
    if invalids: 
        q = '{0} IN ({1})'.format(oid, invalids.rstrip(', '))
        select = arcpy.SelectLayerByAttribute_management(ap, 'NEW_SELECTION', q)

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\checkAP_Invalid_Addresses')

        return(out)
    
    else:
        print_to_stderr('No invalid addresses')    
        return('')

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Invalid_Addresses_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stderr("Starting run... \n")

        # inputs
        # string of path to ap 
        input_ap = arcpy.GetParameterAsText(0)

        print_to_stderr('Finding invalid addresses...')
        out_check = invalidAddress(input_ap)
        if out_check != '':
            print_to_stderr('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stderr("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stdout("Quitting! \n ------------------------------------ \n\n")

