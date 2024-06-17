''' 
GTG, J. Beasley
Data Quality Checks
AP & Parcel - finds address points
with different address than the parcels
they are within. '''


import arcpy
import os
from os import path
import datetime
from datetime import datetime
import logging
import sys
import ast
import time

arcpy.env.overwriteOutput = True
scratch = arcpy.env.scratchWorkspace = arcpy.env.scratchGDB

def print_to_stdout(a):
      print(a)
      logging.info(a)
      sys.stdout.flush()
      time.sleep(1)
     
def print_to_stderr(a):
      sys.stderr.write(a)
      logging.error(a)
      sys.stderr.flush()

def parcelAddPntMismatch(ap, parcel, single_fld_bool):

    parcel_sr = (arcpy.Describe(parcel).spatialReference).name
    ap_sr = (arcpy.Describe(ap).spatialReference).name
    if parcel_sr != ap_sr:
        print_to_stderr('Spatial references of Parcels and Address Points do NOT MATCH!')

    ap_flds = ['AddNum_Pre', 'Add_Number', 'AddNum_Suf', 'St_PreDir',
            'St_Name', 'St_PosTyp', 'St_PosDir']

    if single_fld_bool == 'True':
        parcel_flds = ['FullAdd']
    elif single_fld_bool == 'False':
        parcel_flds = ['AddNum_Pre', 'Add_Number', 'AddNum_Suf', 'St_PreDir',
                        'St_Name', 'St_PosTyp', 'St_PosDir']
    else:
        print_to_stdout("Expected boolean response as text ('True' or 'False'), unaccepatble value given")
        print_to_stderr('Variable single_fld_bool = {}'.format(single_fld_bool))   
        
    desc = arcpy.Describe(ap)
    out_fgdb = desc.path

    # calculate address field in address poitns
    ap_copy = arcpy.CopyFeatures_management(ap, r'in_memory\ap_copy')
    ap_fulladd = 'GTG_apfulladd'
    arcpy.AddField_management(ap_copy, ap_fulladd, 'TEXT')
    ap_cf_exp = '('
    for i, a in enumerate(ap_flds):
        if a != '':
            ap_cf_exp += 'str(!{}!) + " " + '.format(a)
        if i == (len(ap_flds)-1):
            ap_cf_exp = ap_cf_exp.strip(' + " "')
            ap_cf_exp += ').replace("  ", " ").replace("  ", " ").strip().upper()'
    arcpy.CalculateField_management(ap_copy, ap_fulladd, ap_cf_exp, 'PYTHON3')

    # calculate address field in parcels
    parcel_copy = arcpy.CopyFeatures_management(parcel, r'in_memory\parcel_copy')
    parcel_fulladd = 'GTG_parfulladd'
    arcpy.AddField_management(parcel_copy, parcel_fulladd, 'TEXT')
    parcel_cf_exp = '('
    for i, p in enumerate(parcel_flds):
        if p != '':
            parcel_cf_exp += 'str(!{}!) + " " + '.format(p)
        if len(parcel_flds) != 1 and i == (len(parcel_flds)-1):
            parcel_cf_exp = parcel_cf_exp.strip(' + " "')
            parcel_cf_exp += ').strip().upper().replace("NONE", "").replace("  ", " ").replace("  ", " ")'
        elif len(parcel_flds) == 1:
            parcel_cf_exp = parcel_cf_exp.strip(' + " "')
            parcel_cf_exp += ').strip().upper().replace("NONE", "").replace("  ", " ").replace("  ", " ")'
    arcpy.CalculateField_management(parcel_copy, parcel_fulladd, parcel_cf_exp, 'PYTHON3')


    spatjoin = arcpy.SpatialJoin_analysis(ap_copy, parcel_copy, r'in_memory\ap_parcel_sj', 'JOIN_ONE_TO_ONE', 'KEEP_ALL', '', 'WITHIN')
    select = arcpy.SelectLayerByAttribute_management(spatjoin, 'NEW_SELECTION', 'GTG_apfulladd <> GTG_parfulladd')

    if arcpy.GetCount_management(select)[0] != '0':
        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\check_AP_Parcel_Mismatch')

        keep_flds = ['OBJECTID', 'AP_ID_GeoAdd', 'GTG_apfulladd', 'GTG_parfulladd']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)

    else:

        print_to_stdout('No parcels are mismatched with address points')
        return('')


def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\AP_Parcel_Mismatch_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path to ap 
        input_ap = arcpy.GetParameterAsText(0)
        # string of path to parcel
        input_parcel = arcpy.GetParameterAsText(1)
        single_add_fld = arcpy.GetParameterAsText(2) 

        print_to_stdout('Finding invalid addresses...')
        out_check = parcelAddPntMismatch(input_ap, input_parcel, single_add_fld)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

