''' 
GTG, J. Beasley
Data Quality Checks
Multipart Boundaries - Boundaries
This script identifies multipart 
polygons in boundary layers. '''


import arcpy
import os
from os import path
import datetime
from datetime import datetime
import logging
import sys
import time 
import ast

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

def multipartBnd(bnd):

    desc = arcpy.Describe(bnd)
    out_fgdb = desc.path

    bnd_name = arcpy.Describe(bnd).baseName
    print_to_stdout('Working on {}'.format(bnd_name))

    oid = 'OBJECTID'

    multiparts = ''

    with arcpy.da.SearchCursor(bnd, [oid, 'SHAPE@']) as scur:
        for row in scur:
            if row[1].isMultipart:
                multiparts += (str(row[0]) + ', ')

    if multiparts != '':

        q = '{0} IN ({1})'.format(oid, multiparts.rstrip(', '))
        select = arcpy.SelectLayerByAttribute_management(bnd, 'NEW_SELECTION', q)

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\checkBND_{0}_Multipart_Polygons'.format(bnd_name))
        arcpy.AddField_management(out, 'BoundaryName', 'TEXT', field_alias='Boundary Layer Name')
        arcpy.CalculateField_management(out, 'BoundaryName', "'{}'".format(bnd_name), 'PYTHON3')

        flds = arcpy.ListFields(out)
        for f in flds:
            if ((f.name).split('_'))[-1] == 'GeoAdd':
                geoadd_fld = str(f.name)

        arcpy.AddField_management(out, 'ID_GeoAdd', 'TEXT', field_alias='GeoAddresser ID')
        arcpy.CalculateField_management(out, 'ID_GeoAdd', "!{}!".format(geoadd_fld), 'PYTHON3')

        keep_flds = ['OBJECTID', 'BoundaryName', 'ID_GeoAdd']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)

    else:

        print_to_stdout('No multipart polygons here.')
        return('')

def combineOuts(bnds):

    desc = arcpy.Describe(bnds[0])
    out_fgdb = desc.path

    out = arcpy.Merge_management(bnds, out_fgdb + r'\checkBND_Multipart_Polygons')

    # cleanup, aisle 6
    if isinstance(bnds, list):
        for s in bnds:
            arcpy.Delete_management(s)
    else:
        arcpy.Delete_management(bnds)

    keep_flds = ['OBJECTID', 'BoundaryName', 'ID_GeoAdd']
    all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
    del_flds = [f for f in all_flds if f not in keep_flds]
    if del_flds:
        arcpy.DeleteField_management(out, del_flds)  

    return(out)
    
def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Multipart_Boundaries_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        input_bnd = ast.literal_eval(arcpy.GetParameterAsText(0))

        print_to_stdout('Finding multipart polygons...')
        if isinstance(input_bnd, list):
            output_bnd = []
            for bnd in input_bnd:
                out_bnd = multipartBnd(bnd)
                if out_bnd != '':
                    output_bnd.append(out_bnd)
            if output_bnd:
                out_check = combineOuts(output_bnd)
                print_to_stdout('Adding review status field...')
                addReviewField(out_check)
        elif isinstance(input_bnd, str):
            out_bnd = multipartBnd(input_bnd)
            if out_bnd != '':
                out_check = combineOuts(out_bnd)
                print_to_stdout('Adding review status field...')
                addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

