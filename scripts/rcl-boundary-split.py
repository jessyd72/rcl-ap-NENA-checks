''' 
GTG, J. Beasley
Data Quality Checks
Boundary Split - finds segments 
that are not split at the crossing 
of a boundary polygon'''


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

def splitRoadAtBnd(rcl, bnd):

    bnd_sr = (arcpy.Describe(bnd).spatialReference).name
    rcl_sr = (arcpy.Describe(rcl).spatialReference).name
    if bnd_sr != rcl_sr:
        print_to_stderr('Spatial references of Boundaries and Road Centerlines do NOT MATCH!')

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    bnd_name = arcpy.Describe(bnd).baseName
    print_to_stdout('Working on {}'.format(bnd_name))

    split_lines = arcpy.CreateFeatureclass_management(out_fgdb, 'split_lines', 'POLYLINE', spatial_reference = rcl)
    arcpy.AddField_management(split_lines, 'ORIG_FID', 'LONG')

    bnd_intersect = arcpy.Intersect_analysis([bnd, rcl], r'in_memory\rcl_bnd_int', 'ALL', output_type='POINT')
    pnt_uid = 'PntUID'
    arcpy.AddField_management(bnd_intersect, pnt_uid, 'TEXT')

    if arcpy.GetCount_management(bnd_intersect)[0] != '0':

        print_to_stdout('Updating unique ID field for intersection points...')
        uid = 0
        with arcpy.da.UpdateCursor(bnd_intersect, [pnt_uid]) as ucur:
            for row in ucur:
                uid += 1
                row[0] = 'id{}'.format(str(uid))
                ucur.updateRow(row)
        del(ucur, row)

        ## tool licensed for adv only
        # split = arcpy.SplitLineAtPoint_management(rcl, bnd_intersect, r'in_memory\split_lines')
        ##################################

        # making copy to densify, line geom not accurate if true curves exist
        copy_rcl = arcpy.CopyFeatures_management(rcl, r'in_memory\rcl_copy')
        # select roads to decrease loop
        select_rcl = arcpy.SelectLayerByLocation_management(copy_rcl, 'INTERSECT', bnd_intersect, selection_type='NEW_SELECTION')
        densify_rcl = arcpy.Densify_edit(select_rcl)   

        line_dict = dict((l[0], l[1]) for l in arcpy.da.SearchCursor(densify_rcl, ['RCL_ID_GeoAdd', 'SHAPE@']))
        pnt_dict = dict((p[0], p[1]) for p in arcpy.da.SearchCursor(bnd_intersect, [pnt_uid, 'SHAPE@']))

        pnt_list = [[x[0], x[1]] for x in arcpy.da.SearchCursor(bnd_intersect, ['SHAPE@', pnt_uid])]
        line_list = [[y[0], y[1]] for y in arcpy.da.SearchCursor(densify_rcl, ['SHAPE@', 'RCL_ID_GeoAdd'])]

        lines_pnts_dict = {}

        for l in line_list:
            for p in pnt_list:
                if l[0].contains(p[0]):
                    # print_to_stdout('Line ID: {0}, Point ID: {1}'.format(l[1], str(p[1])))
                    if not l[1] in lines_pnts_dict:
                        lines_pnts_dict[l[1]] = p[1]
                    else:
                        lines_pnts_dict[l[1]] = (lines_pnts_dict[l[1]], p[1])

        for key_line in lines_pnts_dict.keys():
            pntID = lines_pnts_dict.get(key_line)
            if not isinstance(pntID, tuple):
                input_pnt_geo = pnt_dict.get(pntID)
                multipnts = input_pnt_geo
            else:
                merge_pnt_geo = arcpy.Array()
                for pnt_elem in pntID:
                    input_pnt_geo = pnt_dict.get(pnt_elem)
                    if input_pnt_geo:
                        merge_pnt_geo.add(input_pnt_geo.centroid)
                        multipnts = arcpy.Multipoint(merge_pnt_geo, (arcpy.Describe(rcl)).spatialReference)
            line_geom = line_dict.get(key_line)
            buff_pnt = multipnts.buffer(0.01)
            intersect_line = buff_pnt.intersect(line_geom, 2)
            symm_diff = intersect_line.symmetricDifference(line_geom)
            single_part = arcpy.MultipartToSinglepart_management(symm_diff, r'in_memory\single_part_line')
            arcpy.Append_management(single_part, split_lines, 'NO_TEST')
        
        spat_join = arcpy.SpatialJoin_analysis(split_lines, densify_rcl, r'in_memory\spat_join', 'JOIN_ONE_TO_ONE', 'KEEP_ALL', '', 'WITHIN')        
        ################################
        ## old process when we used split line at point 
        # select = arcpy.SelectLayerByLocation_management(rcl, 'ARE_IDENTICAL_TO', split, invert_spatial_relationship='INVERT')

        out = arcpy.CopyFeatures_management(spat_join, out_fgdb + r'\checkRCL_{0}_Boundary_Split'.format(bnd_name))
        arcpy.AddField_management(out, 'BoundaryName', 'TEXT', field_alias='Boundary Layer Name')
        arcpy.CalculateField_management(out, 'BoundaryName', "'{}'".format(bnd_name), 'PYTHON3')

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', 'BoundaryName']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        arcpy.Delete_management(split_lines)
        arcpy.Delete_management('in_memory')

        return(out)

    else:
        print_to_stdout('Boundary does not intersect with roads')
        return('')

def combineOuts(splits):

    desc = arcpy.Describe(splits[0])
    out_fgdb = desc.path

    out = arcpy.Merge_management(splits, out_fgdb + r'\checkRCL_Boundary_Split')

    # cleanup, aisle 6
    if isinstance(splits, list):
        for s in splits:
            arcpy.Delete_management(s)
    else:
        arcpy.Delete_management(splits)

    keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', 'BoundaryName']
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
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Boundary_Split_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path to bnd and rcl
        input_rcl = arcpy.GetParameterAsText(0)
        input_bnd = ast.literal_eval(arcpy.GetParameterAsText(1))

        print_to_stdout('Finding roads that are not split at boundaries...')
        if isinstance(input_bnd, list):
            if len(input_bnd) > 1:
                output_splits = []
                print_to_stdout('Multiple boundaries... Looping')
                for bnd in input_bnd:
                    out_split = splitRoadAtBnd(input_rcl, bnd)
                    if out_split != '':
                        output_splits.append(out_split)
                if output_splits:
                    out_check = combineOuts(output_splits)
                    print_to_stdout('Adding review status field...')
                    addReviewField(out_check)
            elif len(input_bnd) == 1:
                bnd = input_bnd[0]
                out_split = splitRoadAtBnd(input_rcl, bnd)
                if out_split != '':
                    out_check = combineOuts(out_split)
                    print_to_stdout('Adding review status field...')
                    addReviewField(out_check)
        elif isinstance(input_bnd, str):
            out_split = splitRoadAtBnd(input_rcl, input_bnd)
            if out_split != '':
                out_check = combineOuts(out_split)
                print_to_stdout('Adding review status field...')
                addReviewField(out_check)
        else:
            print_to_stderr('Input boundaries were not received in an acceptable type.')
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

