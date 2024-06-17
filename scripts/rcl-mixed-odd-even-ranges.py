''' 
GTG, J. Beasley

Data Quality Checks
Odd/Even Ranges - Road Centerline

This script will find road segments that have
a parity of ODD but the to or from range is even,
or vice-versa. Parity of BOTH will be considered. '''

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

def oddEvenRanges(rcl, LR):
    
    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    if LR == 'LEFT':
        fromadd = 'FromAddr_L'
        toadd = 'ToAddr_L'
        parity = 'Parity_L'
        out_path = out_fgdb + r'\left_check'
    elif LR =='RIGHT':
        fromadd = 'FromAddr_R'
        toadd = 'ToAddr_R'
        parity = 'Parity_R'
        out_path = out_fgdb + r'\right_check'
    else:
        print_to_stderr('No valid Left/Right parameter given. Must be "LEFT" or "RIGHT"')

    q = "((MOD({0},2)=0 AND MOD({1},2)=0) AND {2} <> 'E') OR \
    ((MOD({0},2)=1 AND MOD({1},2)=1) AND {2} <> 'O') OR \
    ((MOD({0},2)=1 AND MOD({1},2)=0) AND {2} <> 'B') OR \
    ((MOD({0},2)=0 AND MOD({1},2)=1) AND {2} <> 'B')".format(fromadd, toadd, parity)

    select_1 = arcpy.SelectLayerByAttribute_management(rcl, 'NEW_SELECTION', q)

    select_2 = arcpy.SelectLayerByAttribute_management(select_1, 'REMOVE_FROM_SELECTION', "{0} = 0 AND {1} = 0 AND {2} = 'Z'".format(fromadd, toadd, parity))
    
    if arcpy.GetCount_management(select_2)[0] != '0':

        out = arcpy.CopyFeatures_management(select_2, out_path)
        arcpy.AddField_management(out, 'ErrorSide', 'TEXT', field_alias='Error Side')

        return(out)

    else:

        print_to_stdout('No mixed odd/even ranges on {} side'.format(LR))
        return('')

def combineOuts(right, left):

    desc = arcpy.Describe(right)
    out_fgdb = desc.path

    out = arcpy.CopyFeatures_management(right, out_fgdb + r'\checkRCL_Odd_Even_Ranges')

    arcpy.CalculateField_management(out, 'ErrorSide', "'RIGHT'", 'PYTHON3')

    popb_lyr = arcpy.SelectLayerByLocation_management(out, 'ARE_IDENTICAL_TO', left, '', 'NEW_SELECTION')
    if arcpy.GetCount_management(popb_lyr)[0] != '0':
        arcpy.CalculateField_management(popb_lyr, 'ErrorSide', "'BOTH'", 'PYTHON3')

    popl_lyr = arcpy.SelectLayerByLocation_management(left, 'ARE_IDENTICAL_TO', out, '', 'NEW_SELECTION', 'INVERT')
    arcpy.Append_management(popl_lyr, out, 'TEST')

    with arcpy.da.UpdateCursor(out, ['ErrorSide'], 'ErrorSide IS NULL') as ucur:
        for row in ucur:
            row[0] = 'LEFT'
            ucur.updateRow(row)

    # cleanup, aisle 6
    arcpy.Delete_management(right)
    arcpy.Delete_management(left)

    keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', 'ErrorSide', 'FromAddr_L', 'FromAddr_R', 'ToAddr_L', 'ToAddr_R', 'Parity_L', 'Parity_R']
    all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
    del_flds = [f for f in all_flds if f not in keep_flds]
    arcpy.DeleteField_management(out, del_flds)  

    return(out)

def completeOutput(mixed, LR):

    desc = arcpy.Describe(mixed)
    out_fgdb = desc.path

    if LR == 'LEFT':
        fromadd = 'FromAddr_L'
        toadd = 'ToAddr_L'
        parity = 'Parity_L'
    elif LR =='RIGHT':
        fromadd = 'FromAddr_R'
        toadd = 'ToAddr_R'
        parity = 'Parity_R'
    else:
        print_to_stderr('No valid Left/Right parameter given. Must be "LEFT" or "RIGHT"')

    out = arcpy.CopyFeatures_management(mixed, out_fgdb + r'\checkRCL_Odd_Even_Ranges')

    arcpy.CalculateField_management(out, 'ErrorSide', "'{}'".format(LR), 'PYTHON3')

    arcpy.Delete_management(mixed)

    keep_flds = ['OBJECTID', 'RCL_ID_GeoAdd', 'ErrorSide', fromadd, toadd, parity]
    all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
    del_flds = [f for f in all_flds if f not in keep_flds]
    arcpy.DeleteField_management(out, del_flds)  

    return(out)

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')

if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\Mixed_Odd_Even_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        rcl = arcpy.GetParameterAsText(0)

        print_to_stdout('Finding mixed odd/even ranges and parities...')
        left = oddEvenRanges(rcl, 'LEFT')
        right = oddEvenRanges(rcl, 'RIGHT')
        if left != '' and right != '':
            print_to_stdout('Combining left and right outputs...')        
            out_check = combineOuts(right, left)        
            addReviewField(out_check)
        elif left != '' and right == '':
            print_to_stdout('Compiling results...')
            out_check = completeOutput(left, 'LEFT')
            addReviewField(out_check)
        elif left == '' and right != '':
            print_to_stdout('Compiling results...')
            out_check = completeOutput(right, 'RIGHT')
            addReviewField(out_check)

        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:
        logging.error("EXCEPTION OCCURRED",exc_info=True)
        print_to_stdout("Quitting! \n ------------------------------------ \n\n")
