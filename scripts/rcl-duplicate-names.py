''' 
GTG, J. Beasley
Data Quality Checks
RCL - Duplicate Names
Finds duplicate street names 
in different postal codes.'''

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

def duplicateNames(rcl):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    premod = 'St_PreMod'
    predir = 'St_PreDir'
    pretype = 'St_PreTyp'
    presep = 'St_PreSep'
    name = 'St_Name'
    postype = 'St_PosTyp'
    posdir = 'St_PosDir'
    posmod = 'St_PosMod'
    lzip = 'PostCode_L'
    rzip = 'PostCode_R'

    #  Scenarios ->
    # - stname not in dict
    # - stname not in dict, equal zips
    # - stname not in dict, unequal zips
    # - stname in dict
    # - stname in dict, equal zips
    # - stname in dict, equal zips, not in vals (FLAG)
    # - stname in dict, equal zips, in vals
    # - stname in dict, unequal zips, L&R not in vals (FLAG)
    # - stname in dict, unequal zips, L not & R is (add L)
    # - stname in dict, unequal zips, L is & R not (add R)
    # - stname in dict, unequal zips, L is & R is

    stname_dict = {}
    repeats = []
    with arcpy.da.SearchCursor(rcl, [premod, predir, pretype, presep, name, postype, posdir, posmod, lzip, rzip]) as scur:
        for row in scur:
            stname = (' '.join([str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7])])).replace('  ', ' ').replace('  ',' ').strip()
            if stname not in stname_dict.keys(): # if street name not in dict
                if row[8] == row[9]: # if zips equal, add one
                    stname_dict[stname] = [row[8]]
                else: # if zips unequal, add both
                    stname_dict[stname] = [row[8]]
                    stname_dict[stname] = [row[9]]
            else: # if street name is in dict
                zips = stname_dict[stname] 
                if row[8] == row[9]: 
                    if row[8] not in zips: # if zip not in existing list
                        repeats.append(stname) # mark stname as duplicate
                        stname_dict[stname].append(row[8]) # add zip to values, avoid repeat flagging
                    else: # if zip is in list, do nothing
                        pass
                else: 
                    if row[8] not in zips: # lzip not in values
                        if row[9] not in zips: # AND rzip not in values
                            repeats.append(stname) # mark stname as duplicate
                            stname_dict[stname].append(row[8]) # add both zips to values, avoid repeat flagging
                            stname_dict[stname].append(row[9]) # add both zips to values, avoid repeat flagging 
                        else: # lzip not in values, rzip is
                            stname_dict[stname].append(row[8]) # add lzip, avoid repeat flagging
                            pass # move on
                    else: # lzip in vlaues
                        if row[9] not in zips: # lzip in values, rzip is not
                            stname_dict[stname].append(row[9]) # add rzip, avoid repeat flagging
                        else: # lzip AND rzip in values
                            pass

    out = arcpy.CopyFeatures_management(rcl, r'in_memory\copy_rcl')
    arcpy.AddFields_management(out, [['FullStName', 'TEXT', 'Full St Name'], ['AllZips', 'TEXT', 'All Known Zips']])
    exp = "(' '.join([str(!{0}!),str(!{1}!),str(!{2}!),str(!{3}!),str(!{4}!),str(!{5}!),str(!{6}!),str(!{7}!)])).replace('  ', ' ').replace('  ',' ').strip()".format(premod, predir, pretype, presep, name, postype, posdir, posmod)
    arcpy.CalculateField_management(out, 'FullStName', exp, 'PYTHON3')   

    q = 'FullStName in ('
    for i, r in enumerate(repeats):
        if i != (len(repeats)-1):
            q += "'{}', ".format(r) 
        else:
            q += "'{}')".format(r)

    select = arcpy.SelectLayerByAttribute_management(out, 'NEW_SELECTION', q)

    if arcpy.GetCount_management(select)[0] != '0':
        final = arcpy.CopyFeatures_management(select, out_fgdb + r'\check_RCL_Duplicate_Name')

        with arcpy.da.UpdateCursor(final, ['FullStName', 'AllZips']) as ucur:
            for row in ucur:
                allzip = ', '.join(stname_dict[row[0]])
                row[1] = allzip
                ucur.updateRow(row)

        keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', 'FullStName', 'AllZips']
        all_flds = [str(f.name) for f in arcpy.ListFields(final) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(final, del_flds)  

        return(final)
    
    else:

        print_to_stdout('No duplicate street names found')
        return('')

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\RCL_Duplicate_Names_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs
        # string of path
        input_rcl = arcpy.GetParameterAsText(0)
        
        print_to_stdout('Finding RCL with duplicate names...')
        out_check = duplicateNames(input_rcl)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

