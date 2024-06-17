''' 
GTG, J. Beasley

Data Quality Checks
Non-planarized Intersection - Road Centerline

This script will find road segments with non-
planar intersections. '''


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

def splitLineAtPoint(line, point, out_split):

    # making copy to densify, line geom not accurate if true curves exist
    copy = arcpy.CopyFeatures_management(line, r'in_memory\line_copy')
    densify = arcpy.Densify_edit(copy)   

    line_dict = dict((l[0], l[1]) for l in arcpy.da.SearchCursor(densify, ['OBJECTID', 'SHAPE@']))
    pnt_dict = dict((p[0], p[1]) for p in arcpy.da.SearchCursor(point, ['OBJECTID', 'SHAPE@']))

    pnt_list = [[x[0], x[1]] for x in arcpy.da.SearchCursor(point, ['SHAPE@', 'OBJECTID'])]
    line_list = [[y[0], y[1]] for y in arcpy.da.SearchCursor(densify, ['SHAPE@', 'OBJECTID'])]

    lines_pnts_dict = {}

    for l in line_list:
        for p in pnt_list:
            # if point falls on line
            if l[0].contains(p[0]):
                # add the line ID as key and point IDs as values to dict
                if not l[1] in lines_pnts_dict:
                    lines_pnts_dict[l[1]] = p[1]
                else:
                    lines_pnts_dict[l[1]] = (lines_pnts_dict[l[1]], p[1])

    for key_line in lines_pnts_dict.keys():
        # for each line ID, get point IDs
        pntID = lines_pnts_dict.get(key_line)
        # if just one point on line
        if not isinstance(pntID, tuple):
            input_pnt_geo = pnt_dict.get(pntID)
            multipnts = input_pnt_geo
        # if multiple points on line
        else:
            merge_pnt_geo = arcpy.Array()
            for pnt_elem in pntID:
                input_pnt_geo = pnt_dict.get(pnt_elem)
                if input_pnt_geo:
                    merge_pnt_geo.add(input_pnt_geo.centroid)
                    # create multipoint geometry object for splitting
                    multipnts = arcpy.Multipoint(merge_pnt_geo, (arcpy.Describe(point)).spatialReference)
        line_geom = line_dict.get(key_line)
        # buffer to ensure intersection
        buff_pnt = multipnts.buffer(0.01)
        intersect_line = buff_pnt.intersect(line_geom, 2)
        symm_diff = intersect_line.symmetricDifference(line_geom)
        single_part = arcpy.MultipartToSinglepart_management(symm_diff, r'in_memory\single_part_line')
        arcpy.Append_management(single_part, out_split, 'NO_TEST')
    
    spat_join = arcpy.SpatialJoin_analysis(out_split, densify, r'in_memory\spat_join', 'JOIN_ONE_TO_ONE', 'KEEP_ALL', '', 'WITHIN') 

    return(spat_join)       
    
      
def planarizeInt(rcl):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    # lines to be split at intersections
    split_lines_empty = arcpy.CreateFeatureclass_management(out_fgdb, 'split_lines', 'POLYLINE', spatial_reference = rcl)
    arcpy.AddField_management(split_lines_empty, 'ORIG_FID', 'LONG')

    # dissolve to get intersection points
    dissolve = arcpy.Dissolve_management(rcl, r'in_memory\dissolve', '', '', 'SINGLE_PART', 'DISSOLVE_LINES')
    intersect = arcpy.Intersect_analysis(dissolve, r'in_memory\intersect', '', '', 'POINT')
    diss_pnts = arcpy.Dissolve_management(intersect, r'in_memory\diss_pnts', '', '', 'SINGLE_PART', 'DISSOLVE_LINES')

    # select where dissolved roads and orig roads are not identical
    rcl_select = arcpy.SelectLayerByLocation_management(rcl, 'ARE_IDENTICAL_TO', dissolve, invert_spatial_relationship='INVERT')
    pnt_select = arcpy.SelectLayerByLocation_management(diss_pnts, 'INTERSECT', rcl_select)

    split_lines = splitLineAtPoint(rcl_select, pnt_select, split_lines_empty)

    if arcpy.GetCount_management(split_lines)[0] != '0':

        out = arcpy.CopyFeatures_management(split_lines, out_fgdb + r'\checkRCL_Non_Planar_Intersections')

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        arcpy.Delete_management('in_memory')

        return(out)

    else:

        print_to_stdout('All lines are planar')
        return('')


def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')


if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Non_Planar_Intersections_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path to rcl
        input_rcl = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding nonplanar intersections...')
        out_check = planarizeInt(input_rcl)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

