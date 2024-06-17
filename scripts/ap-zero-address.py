''' 
GTG, J. Beasley
Data Quality Checks
AP - finds addresses 
with a zero house number.'''


import arcpy
import os
from os import path
import datetime
from datetime import datetime
import logging
import sys
import ast 
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
      
def zeroAddress(ap):

    desc = arcpy.Describe(ap)
    out_fgdb = desc.path

    select = arcpy.SelectLayerByAttribute_management(ap, 'NEW_SELECTION', 'Add_Number = 0')

    if arcpy.GetCount_management(select)[0] != '0':

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\checkAP_Zero_Addresses')

        keep_flds = ['OBJECTID', 'AP_ID_GeoAdd', 'Add_Number']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)
    
    else:

        print_to_stdout('No zero addresses')
        return('')


def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Zero_Addresses_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path to ap
        input_ap = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding zero addresses...')
        out_check = zeroAddress(input_ap)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

