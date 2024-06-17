''' 
GTG, J. Beasley

Data Quality Checks
Null and Zero Speed Limits - Road Centerline

This script will find road segments with zero
or nulled speed limits. '''

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
      
def checkSpeedLimits(rcl):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    speed_fld = 'SpeedLimit'

    q = '{0} IS NULL OR {0} = 0 OR {0} < 5'.format(speed_fld)
    select = arcpy.SelectLayerByAttribute_management(rcl, 'NEW_SELECTION', q)

    if arcpy.GetCount_management(select)[0] != '0':

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\checkRCL_Zero_Null_Speed_Limit')

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', speed_fld]
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)

    else:

        print_to_stdout('No invalid speed limits found')
        return('')

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')


if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Zero_Null_Speed_Limits_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        logging.info("Starting run... \n")

        # inputs
        # string of path to rcl
        input_rcl = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding zero and null speed limits...')
        out_check = checkSpeedLimits(input_rcl)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stdout("Quitting! \n ------------------------------------ \n\n")

