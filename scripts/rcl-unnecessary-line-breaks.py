''' 
GTG, J. Beasley

Data Quality Checks
Unnecessary line breaks - Road Centerline

This script will find road segments with
unnecessary line breaks. Manual review of
address ranges is required to update. '''


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
    

def checkLineBreaks(rcl):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    intersect_rcl = arcpy.Intersect_analysis(rcl, r'in_memory\intersect', 'ALL', '', 'POINT')

    dissolve_stname = arcpy.Dissolve_management(rcl, r'in_memory\dissolve','St_Name', '', 'SINGLE_PART', 'DISSOLVE_LINES')
    diss_int_stname = arcpy.Intersect_analysis(dissolve_stname, r'in_memory\intersect_diss', 'ALL', '', 'POINT')

    pnt_select = arcpy.SelectLayerByLocation_management(intersect_rcl, 'INTERSECT', diss_int_stname, '', 'NEW_sELECTION', 'INVERT')

    rcl_select = arcpy.SelectLayerByLocation_management(rcl, 'INTERSECT', pnt_select, '', 'NEW_SELECTION')

    if arcpy.GetCount_management(rcl_select)[0] != '0':

        out = arcpy.CopyFeatures_management(rcl_select, out_fgdb + r'\checkRCL_Unnecessary_Line_Breaks')

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)

    else:

        print_to_stdout('No unnecessary line breaks found')
        return('')

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')


if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Unnecessary_Line_Breaks_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path to rcl
        input_rcl = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding unnecessary line breaks...')
        out_check = checkLineBreaks(input_rcl)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

