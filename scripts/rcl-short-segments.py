''' 
GTG, J. Beasley

Data Quality Checks
Short Segment - Road Centerline

This script finds short segments, 
where a minimum of 10 feet is default'''


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
      
def findShortSegments(rcl, l):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    conv_dict = {'FEET': 0.3048, 'INCHES': 0.0254,'YARDS': 0.9144,'MILES': 1609.34, 'METERS': 1, 'KILOMETERS': 1000, 
                'DECIMETERS': 0.1, 'CENTIMETERS': 0.01, 'MILIMETERS': 0.001, 'NAUTICAL-MILES': 1852}

    # if no length, default to 10 feet
    u = 1
    if l == '':
        u = 0
        l = '3.048 Meters'
        length = 3.048
        print_to_stdout('No length provided, defaulting to: {}'.format(l))

    else:
        len_str, unit = l.split(' ')

        if unit.upper() in conv_dict.keys():
            cf = conv_dict[unit.upper()]
            length = float(len_str) * cf
            print_to_stdout('Length threshold: {} Meters'.format(str(length)))

    shorties = []

    # working in WKID 3857, WGS84 Web Mercator, to avoid unexpected projections/measurements 
    with arcpy.da.SearchCursor(rcl, ['RCL_ID_GeoAdd', 'SHAPE@'], spatial_reference = arcpy.SpatialReference(3857)) as scur:
       for row in scur:
           if row[1].getLength('GEODESIC', 'METERS') < length:
               shorties.append(row[0])

    q = "RCL_ID_GeoAdd in ("
    for i, r in enumerate(shorties):
        if i != (len(shorties)-1):
            q += "'{}', ".format(r) 
        else:
            q += "'{}')".format(r)

    select = arcpy.SelectLayerByAttribute_management(rcl, 'NEW_SELECTION', q)

    if arcpy.GetCount_management(select)[0] != '0':

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\checkRCL_Short_Segments')

        if u == 1:
            arcpy.AddField_management(out, 'UserLenMin', 'TEXT', field_alias='User Specified Min. Length')
            arcpy.CalculateField_management(out, 'UserLenMin', "'{}'".format(l.title()))

        arcpy.AddField_management(out, 'LenMin_m', 'TEXT', field_alias='Length Minimum (meters)')
        arcpy.CalculateField_management(out, 'LenMin_m', "'{} Meters'".format(str(length)))

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', 'LenMin_m', 'UserLenMin']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)
    
    else:

        print_to_stdout('No short segments found')
        return('')


def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')


if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Short_Segments_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path to rcl
        input_rcl = arcpy.GetParameterAsText(0)
        length = arcpy.GetParameterAsText(1)

        print_to_stdout('Finding short segments...')
        out_check = findShortSegments(input_rcl, length)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stdout("Quitting! \n ------------------------------------ \n\n")

