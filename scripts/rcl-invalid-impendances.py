''' 
GTG, J. Beasley

Data Quality Checks
Invalid Impedences - Road Centerline

This script find invalid impadences in
oneway field. Values ot equal to 
FT, TF, or B.'''


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
      
def invalidImpedances(rcl):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    oneway_fld = 'OneWay'

    q = "{0} NOT IN ('TF', 'FT', 'B')".format(oneway_fld)
    print_to_stdout(q)
    select = arcpy.SelectLayerByAttribute_management(rcl, 'NEW_SELECTION', q)

    if arcpy.GetCount_management(select)[0] != '0':

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\checkRCL_Invalid_Impedances')

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', oneway_fld]
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)

    else:

        print_to_stdout('No invalid oneway impedences found')
        return('')

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')


if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Invalid_Impedances_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path to rcl
        input_rcl = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding multipart segments...')
        out_check = invalidImpedances(input_rcl)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

