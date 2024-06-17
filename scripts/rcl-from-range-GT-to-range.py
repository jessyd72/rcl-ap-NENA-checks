''' 
GTG, J. Beasley

Data Quality Checks
From Range > To Range - Road Centerline

This script will find road segments that have
a From-range greater than the To-range. '''


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
      
def print_to_stderr(a):
      sys.stderr.write(a)
      logging.error(a)
      sys.stderr.flush()

def FTRanges(rcl):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    lf = 'FromAddr_L'
    lt = 'ToAddr_L'
    rf = 'FromAddr_R'
    rt = 'ToAddr_R'

    q = '({0} > {1}) OR ({2} > {3})'.format(lf, lt, rf, rt)

    select = arcpy.SelectLayerByAttribute_management(rcl, 'NEW_SELECTION', q)

    if arcpy.GetCount_management(select)[0] != '0':

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\checkRCL_From_GT_To')

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', lf, lt, rf, rt]
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  
        
        return(out)

    else:

        print_to_stdout('No from ranges greater than to ranges.')
        return('')

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Frm_GT_To_log_{0}_{1}.txt'.format(current.month, current.year))))
        print_to_stdout(logfile)
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path to rcl
        input_rcl = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding from ranges GT to ranges...')
        out_check = FTRanges(input_rcl)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED",exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")