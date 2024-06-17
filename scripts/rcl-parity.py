''' 
GTG, J. Beasley
Data Quality Checks
RCL - Parity
Finds segments where 
left and right parity  
are both even or odd'''

import arcpy
import json
import os
from os import path
import datetime               
from datetime import datetime
import logging
import ast
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

def checkParity(rcl):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    rparity = 'Parity_R'
    lparity = 'Parity_L'

    q = "({0} = {1}) AND {0} NOT IN ('B', 'Z') AND {1} NOT IN ('B', 'Z')".format(rparity, lparity)
    select = arcpy.SelectLayerByAttribute_management(rcl, 'NEW_SELECTION', q)

    if arcpy.GetCount_management(select)[0] != '0':
    
        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\check_RCL_parity')

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', rparity, lparity]
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return out

    else:
        print_to_stdout('No segments found with both even or odd parity')
        return('')


def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\RCL_parity_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path
        input_rcl = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding RCL with equal left and right parity...')
        out_check = checkParity(input_rcl)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

