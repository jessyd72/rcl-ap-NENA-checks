''' 
GTG, J. Beasley
Data Quality Checks
AP - Duplicate Addresses
Finds duplicate address with the 
same number, building, unit, street, 
and postal code.'''

import arcpy
import json
import os
from os import path
import datetime               
from datetime import datetime
import logging
import ast
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

def duplicateAddresses(ap):

    addpre = 'AddNum_Pre'
    addnum = 'Add_Number'
    addsuf = 'AddNum_Suf'
    premod = 'St_PreMod'
    predir = 'St_PreDir'
    pretype = 'St_PreTyp'
    presep = 'St_PreSep'
    stname = 'St_Name'
    postype = 'St_PosTyp'
    posdir = 'St_PosDir' 
    posmod = 'St_PosMod'
    postcode = 'Post_Code'
    bldg = 'Building'
    flr = 'Floor'
    unit = 'Unit'

    desc = arcpy.Describe(ap)
    out_fgdb = desc.path

    adds = {}
    repeat_oids = []
    with arcpy.da.SearchCursor(ap, [addpre, addnum, addsuf, premod, predir, pretype, presep, 
                                    stname, postype, posdir, posmod, postcode, bldg, flr, unit, 'AP_ID_GeoAdd']) as scur:
        for row in scur:
            add = [str(x) for x in [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], 
                                    row[8], row[9], row[10], row[11], row[12], row[13], row[14]]]
            finaladd = (' '.join(add)).replace('None',' ').replace('  ', ' ').replace('  ',' ').replace('  ',' ').strip()
            if finaladd not in adds.keys():
                adds[finaladd] = str(row[15])
            else:
                repeat_oids.append(str(row[15]))
                repeat_oids.append(adds[finaladd])

    if repeat_oids:

        q = 'AP_ID_GeoAdd in ('
        for i, r in enumerate(list(set(repeat_oids))):
            if i != (len(repeat_oids)-1):
                q += "'{}', ".format(r) 
            else:
                q += "'{}')".format(r)
        print_to_stdout(q)

        out = arcpy.CopyFeatures_management(ap, out_fgdb + '\\check_AP_Duplicate_Addresses')

        select = arcpy.SelectLayerByAttribute_management(out, 'NEW_SELECTION', q, invert_where_clause='INVERT')
        final = arcpy.DeleteRows_management(select)

        keep_flds = ['OBJECTID', 'AP_ID_GeoAdd', addpre, addnum, addsuf, premod, predir, pretype, presep, 
                    stname, postype, posdir, posmod, postcode, bldg, flr, unit,]
        all_flds = [str(f.name) for f in arcpy.ListFields(final) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(final, del_flds)  

        return(final)
    
    else:
        print_to_stdout('No duplicate addresses')    
        return('')

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\AP_Duplicate_Addresses_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stderr("Starting run... \n")

        # inputs
        # string of path
        input_ap = arcpy.GetParameterAsText(0)
        
        print_to_stdout('Finding AP with duplicate names...')
        out_check = duplicateAddresses(input_ap)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

