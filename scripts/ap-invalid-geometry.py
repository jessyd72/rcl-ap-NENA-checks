''' 
GTG, J. Beasley

Data Quality Checks
Invalid Geometry - AP

This script will find address points
with invalid geometry. '''

import arcpy
import json
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

def apCheckGeometry(ap):

    desc = arcpy.Describe(ap)
    out_fgdb = desc.path
    
    invgeom_tab = arcpy.CheckGeometry_management(ap, r'in_memory\ap_invalid_geom', 'ESRI')
    invalid_oids = [str(x[0]) for x in arcpy.da.SearchCursor(invgeom_tab, ['FEATURE_ID'])]
    if invalid_oids:
        q = 'OBJECTID IN ({})'.format((',').join(invalid_oids))
        select = arcpy.SelectLayerByAttribute_management(ap, 'NEW_SELECTION', q)

        select_dict = {r[0]:r[1] for r in arcpy.da.SearchCursor(select, ['OBJECTID', 'AP_ID_GeoAdd'])}
        update_dict = {select_dict[r[0]]:r[1] for r in arcpy.da.SearchCursor(invgeom_tab, ['FEATURE_ID', 'PROBLEM'])}

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\checkAP_Invalid_Geometry')
        arcpy.AddField_management(out, 'GeomProblem', 'TEXT', field_alias='Geometry Problem')
        with arcpy.da.UpdateCursor(out, ['AP_ID_GeoAdd', 'GeomProblem']) as ucur:
            for urow in ucur:
                urow[1] = update_dict[urow[0]]
                ucur.updateRow(urow)

        keep_flds = ['OBJECTID', 'AP_ID_GeoAdd', 'GeomProblem']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)
    
    else:
        print_to_stdout('No invalid geometries')    
        return('')


def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')


if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\AP_Invalid_Geometry_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path 
        input_ap = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding invalid geometries...')
        out_check = apCheckGeometry(input_ap)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

