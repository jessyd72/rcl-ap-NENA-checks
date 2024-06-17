''' 
GTG, J. Beasley
Data Quality Checks

RCL - Finds road class values
that do not follow MTFCC values.'''

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

def CFCCToMTFCC(rcl):

    desc = arcpy.Describe(rcl)
    out_fgdb = desc.path

    roadclass = 'RoadClass'

    rcl_temp = arcpy.CopyFeatures_management(rcl, r'in_memory\RCL_update_Roadclass')
    arcpy.AddField_management(rcl_temp, 'MTFCC_value', 'TEXT', '', '', 15, 'Suggested MTFCC Value')

    mtfcc_desc = ['Primary', 'Secondary', 'Local', 'Vehicular Trail', 'Ramp', 'Service Drive', 
                'Walkway', 'Stairway', 'Alley', 'Private', 'Parking Lot', 'Trail', 'Bridle Path', 'Other']
    mtfcc_codes = {'S1100':'Primary', 'S1200':'Secondary', 'S1400':'Local', 'S1500':'Vehicular Trail', 'S1630':'Ramp', 
                'S1640':'Service Drive', 'S1710':'Walkway', 'S1720':'Stairway', 'S1730':'Alley', 'S1740':'Private',
                'S1780':'Parking Lot', 'S1820':'Trail', 'S1830':'Bridle Path', 'S2000':'Other'}
    cfcc_codes = {'A00':'Other', 'A01':'Secondary', 'A02':'Secondary', 'A03':'Secondary', 'A04':'Secondary',
                'A05':'Secondary', 'A06':'Secondary', 'A07':'Secondary', 'A08':'Secondary',
                'A10':'Primary', 'A11':'Primary', 'A12':'Primary', 'A13':'Primary', 
                'A14':'Primary', 'A15':'Primary', 'A16':'Primary', 'A17':'Primary', 'A18':'Primary', 
                'A20':'Secondary', 'A21':'Secondary', 'A22':'Secondary', 'A23':'Secondary', 
                'A24':'Secondary', 'A25':'Secondary', 'A26':'Secondary', 'A27':'Secondary', 
                'A28':'Secondary', 'A30':'Secondary', 'A31':'Secondary', 'A32':'Secondary', 
                'A33':'Secondary', 'A34':'Secondary', 'A35':'Secondary', 'A36':'Secondary', 
                'A37':'Secondary', 'A38':'Secondary',
                'A40':'Local', 'A41':'Local', 'A42':'Local', 'A43':'Local', 'A45':'Local', 'A46':'Local', 
                'A47':'Local', 'A48':'Local', 
                'A50':'Vehicular Trail', 'A51':'Vehicular Trail', 'A52':'Vehicular Trail', 'A53':'Vehicular Trail',
                'A60':'Other', 'A61':'Other', 'A62':'Other', 
                'A63':'Ramp', 'A64':'Service Drive', 'A70':'Other', 'A71':'Walkway', 'A72':'Stairway', 
                'A73':'Alley', 'A74':'Private', 'A75':'Parking Lot'}

    with arcpy.da.UpdateCursor(rcl_temp, [roadclass, 'MTFCC_value']) as ucur:
        for row in ucur:
            if row[0] in cfcc_codes.keys():
                row[1] = cfcc_codes[row[0]]
            elif row[0] in mtfcc_codes.keys():
                row[1] = mtfcc_codes[row[0]]
            elif row[0] in mtfcc_desc:
                row[1] = None
            else:
                row[1] = 'Manual review'
            ucur.updateRow(row)    

    select = arcpy.SelectLayerByAttribute_management(rcl_temp, 'NEW_SELECTION', 'MTFCC_value IS NOT NULL')

    if arcpy.GetCount_management(select)[0] != '0':

        out = arcpy.CopyFeatures_management(select, out_fgdb + r'\check_RCL_Update_Roadclass')

        keep_flds = ['OBJECTID', 'MTFCC_value', 'RCL_ID_GeoAdd']
        all_flds = [str(f.name) for f in arcpy.ListFields(out) if not f.required]
        del_flds = [f for f in all_flds if f not in keep_flds]
        arcpy.DeleteField_management(out, del_flds)  

        return(out)

    else:

        print_to_stdout('No invalid MTFCC values found')
        return('')

    arcpy.Delete_management('in_memory')

def addReviewField(check_fc):

    arcpy.AddField_management(check_fc, 'ReviewStatus', 'TEXT', field_domain='ReviewStatus')
    arcpy.CalculateField_management(check_fc, 'ReviewStatus', "'Flagged'", 'PYTHON3')
    
if __name__ == '__main__':

    try:

        # maintain log file
        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\RCL_CFCC_to_MTFCC_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')
        print_to_stdout("Starting run... \n")

        # inputs 
        # string of path to rcl
        input_rcl = arcpy.GetParameterAsText(0) 
        
        print_to_stdout('Finding road class values to update to MTFCC...')
        out_check = CFCCToMTFCC(input_rcl)
        if out_check != '':
            print_to_stdout('Adding review status field...')
            addReviewField(out_check)
        
        print_to_stdout("Success! \n ------------------------------------ \n\n")

    except Exception as e:        
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")
