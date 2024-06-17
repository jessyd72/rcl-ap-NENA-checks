''' 
GTG, J. Beasley

Phase I - NENA Schema Compliance 
Mirgation Preparation - Road Centerline and
Address Points
If provided, will also migrate parcels, 
zipcodes, and other boundary layers. 

This script will generate 1 or 2 CSVs containing
the standard NENA schema for RCLs and APs
with field matched of the user's input. 

If CSV notes are acceptable, user's data will
be migrated to NENA schema FGDB'''

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

def createMigrationCSV(input_fc, flds, APorRCL, out_csv):

    if APorRCL == 'RCL':
        nena_flds = json_array['rcl_nena_flds'][0]
    elif APorRCL == 'AP':
        nena_flds = json_array['ap_nena_flds'][0]
    h1 = logging.StreamHandler(sys.stdout)

    print_to_stdout("Creating CSV...") 
    print_to_stdout(out_csv) 
    csv_w = open(out_csv, 'w')
    csv_w.write("NENA Field, NENA Alias, NENA Field Type, M/C/O, User's Field, User's Field Type, Notes \n")

    final_notes = ''

    user_fields = {str(f.name):(str(f.type)).replace('SmallInteger', 'Integer') for f in arcpy.ListFields(input_fc)}

    print_to_stdout("Looping fields...") 

    for f in flds:
        
        try:

            NENA_fld = f[0]
            user_fld = f[1]

            # get NENA details
            NENA_name = nena_flds[NENA_fld][0]
            NENA_type = nena_flds[NENA_fld][1]
            NENA_mco = mco_dict[nena_flds[NENA_fld][2]]

            print_to_stdout('Working on field: {}'.format(NENA_fld)) 

            notes = ''

            if user_fld == '':

                print_to_stdout('No user field provided.')
                
                if NENA_mco == 'Mandatory':
                        notes += 'MUST POPULATE. '
                if NENA_fld == 'Discrepancy Agency ID':
                    notes += 'TO BE POPULATED LATER. '

                csv_w.write('{0}, {1}, {2}, {3}, , , {4} \n'.format(NENA_name, NENA_fld, NENA_type, NENA_mco, notes))

            else:

                # write NENA details
                csv_w.write('{0}, {1}, {2}, {3}, '.format(NENA_name, NENA_fld, NENA_type, NENA_mco))

                # get user's details
                user_fld_type = user_fields[user_fld]
            
                if APorRCL == 'RCL':
                    if NENA_mco == 'Mandatory':
                        notes += 'MANDATORY. '
                    if NENA_fld == 'Discrepancy Agency ID':
                        notes += 'TO BE POPULATED LATER. '
                    if user_fld_type != NENA_type:
                        notes += 'Convert {0} to {1}. '.format(user_fld_type, NENA_type)
                    else:
                        if NENA_type == 'String':
                            s_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))]))
                            if all(s.istitle() for s in s_list) == False and all(s.isupper() for s in s_list) == False and all(s.islower() for s in s_list) == False:
                                notes += 'Consider standardized case. '
                        if NENA_type in ['Integer', 'SmallInteger']:
                            val_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null".format(user_fld))]))
                            if all(c.isdigit() for val in val_list for c in val) == False:
                                notes += 'Found letters/special characters- must update values to be all digits! '
                        if NENA_type == 'Double':
                            val_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null".format(user_fld))]))
                            if all((c.isdigit() or c in ['.', '-']) for val in val_list for c in val) == False:
                                notes += 'Found letters/special characters- must update values to be all digits! '
                        if NENA_fld in ['State_L', 'State_R', 'Country_L', 'Country_R']:
                            state_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))]))
                            if any(len(state) > 2 for state in state_list):
                                notes += 'Must update state to abbreviation- cannot exceed length of 2! '
                        if NENA_fld in ['Parity Left', 'Parity Right']:
                            par_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld])]))
                            if len(list(set(par_list) - set(nena_parity))) != 0:
                                notes += 'Must update values to O/E/B/Z. '
                        if NENA_fld in ['Street Name Pre Directional', 'Street Name Post Directional']:
                            dir_list = list(set([str(x[0]).title().strip() for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))]))
                            if len(list(set(dir_list) - set(nena_dir))) != 0:
                                notes += 'Must update values to spelled out directions (ex. North/East/Southeast/etc.) '
                        if NENA_fld in ['Street Name Pre Type', 'Street Name Post Type']:
                            type_list = list(set([str(x[0]).title().strip() for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))]))
                            if len(list(set(type_list) - set(nena_sttypes))) != 0:
                                notes += 'Found non-standard street types values. View http://technet.nena.org/nrs/registry/StreetNamePreTypesAndStreetNamePostTypes.xml for details. '
                        if NENA_fld == 'Road Class':
                            rc_list = list(set(str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))))
                            if len(list(set(rc_list) - set(nena_mtfcc))) != 0:
                                notes += 'Found unacceptable MTFCC values. View https://www2.census.gov/geo/pdfs/reference/mtfccs2019.pdf for details. '
                        if NENA_fld == 'One-Way':
                            ow_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld])]))
                            if len(list(set(ow_list) - set(nena_oneway))) != 0:
                                notes += 'Must update values to B/TF/FT. '

                    # write user's details
                    csv_w.write('{0}, {1}, {2} \n'.format(user_fld, user_fld_type, notes))

                elif APorRCL == 'AP':
                    if NENA_mco == 'Mandatory':
                        notes += 'MANDATORY. '
                    if NENA_fld == 'Discrepancy Agency ID':
                        notes += 'TO BE POPULATED LATER. '
                    if user_fld_type != NENA_type:
                        notes += 'Convert {0} to {1}. '.format(user_fld_type, NENA_type)
                    else:
                        if NENA_type == 'String':
                            s_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))]))
                            if (all(s.istitle() for s in s_list) == False and all(s.isupper() for s in s_list) == False and all(s.islower() for s in s_list) == False) or all(s.isdigit() for s in s_list) == False:
                                notes += 'Consider standardized case. '
                        if NENA_type in ['Integer', 'SmallInteger']:
                            val_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null".format(user_fld))]))
                            if all(c.isdigit() for val in val_list for c in val) == False:
                                notes += 'Found letters/special characters- must update values to be all digits! '
                        if NENA_type == 'Double':
                            val_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null".format(user_fld))]))
                            if all((c.isdigit() or c in ['.', '-']) for val in val_list for c in val) == False:
                                notes += 'Found letters/special characters- must update values to be all digits! '
                        if NENA_fld in ['State', 'Country']:
                            state_list = list(set([str(x[0]) for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))]))
                            if any(len(state) > 2 for state in state_list):
                                notes += 'Must update state to abbreviation- cannot exceed length of 2! '
                        if NENA_fld in ['Street Name Pre Directional', 'Street Name Post Directional']:
                            dir_list = list(set([str(x[0]).title().strip() for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))]))
                            if len(list(set(dir_list) - set(nena_dir))) != 0:
                                notes += 'Must update values to spelled out directions (ex. North/East/Southeast/etc.) '
                        if NENA_fld in ['Street Name Pre Type', 'Street Name Post Type']:
                            type_list = list(set([str(x[0]).title().strip() for x in arcpy.da.SearchCursor(input_fc, [user_fld], "{0} is not null OR {0} in (' ', '  ')".format(user_fld))]))
                            if len(list(set(type_list) - set(nena_sttypes))) != 0:
                                notes += 'Found unacceptable street types values. View http://technet.nena.org/nrs/registry/StreetNamePreTypesAndStreetNamePostTypes.xml for details. '
                        
                    # write user's details
                    csv_w.write('{0}, {1}, {2} \n'.format(user_fld, user_fld_type, notes))

                else:
                    print_to_stderr('Unacceptable value entered. Must be ''RCL'' or ''AP''')

            final_notes += notes

        except Exception:        
            print_to_stderr("EXCEPTION OCCURRED in for loop") # , exc_info=True)

    print_to_stdout('Final notes read: {}'.format(final_notes)) 

    csv_w.close()

    return(final_notes)

def migrateToFGDB(input_fc, flds, fgdb, NENA_fgdb, out_fldr, APorRCL, sr):

    print_to_stdout('Migrating {}...'.format(APorRCL))

    if APorRCL == 'RCL':
        nena_flds = json_array['rcl_nena_flds'][0]
    elif APorRCL == 'AP':
        nena_flds = json_array['ap_nena_flds'][0]

    fgdb_name = 'GeoAnalyzer_{0}.gdb'.format(timestamp)

    if not arcpy.Exists(fgdb):

        print_to_stdout('Creating working FGDB...')

        arcpy.CreateFileGDB_management(out_fldr, fgdb_name)

        arcpy.CreateDomain_management(fgdb, 'ReviewStatus', 'Review status for GeoAnalyzer checks.', 
                                      'TEXT', 'CODED', 'DEFAULT', 'DEFAULT')
        domain_vals = ['Flagged', 'Acceptable', 'Corrected']
        for d in domain_vals:
            arcpy.AddCodedValueToDomain_management(fgdb, 'ReviewStatus', d, d)     

        arcpy.CreateFeatureDataset_management(fgdb, 'OrigData', sr)
        arcpy.CreateFeatureDataset_management(fgdb, 'GeoAnalyzerData', sr)  

    if APorRCL == 'RCL':

        nena_out = arcpy.FeatureClassToFeatureClass_conversion(nena_fgdb + r'\RoadCenterlines', fgdb + r'\GeoAnalyzerData' , 'RoadCenterlines')
    
        print_to_stdout('Copying user''s RCL over...')
        orig = arcpy.FeatureClassToFeatureClass_conversion(input_fc, fgdb + r'\OrigData', 'orig_RCL')

        print_to_stdout('Adding unique ID field...')

        arcpy.AddField_management(orig, 'RCL_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser RCL ID')
        uid = 0
        with arcpy.da.UpdateCursor(orig, ['RCL_ID_GeoAdd']) as ucur:
            for row in ucur:
                uid += 1
                row[0] = 'RCL_{0}'.format(str(uid))
                ucur.updateRow(row)
        del(ucur, row)

        arcpy.AddField_management(nena_out, 'RCL_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser RCL ID')

        out_flds = []
        orig_flds = []
        for f in flds:
            if f[1] != '':
                orig_flds.append(f[1])
                out_flds.append(str(nena_flds[f[0]][0]))
        orig_flds.append('RCL_ID_GeoAdd')
        out_flds.append('RCL_ID_GeoAdd')
        orig_flds.append('SHAPE@')
        out_flds.append('SHAPE@')

        icur = arcpy.da.InsertCursor(nena_out, out_flds)
        with arcpy.da.SearchCursor(orig, orig_flds) as scur:
            for row in scur:
                icur.insertRow(row)
        del(icur, scur, row)

    elif APorRCL == 'AP':

        nena_out = arcpy.FeatureClassToFeatureClass_conversion(nena_fgdb + r'\SiteStructureAddressPoints', fgdb + r'\GeoAnalyzerData' , 'SiteStructureAddressPoints')

        print_to_stdout('Copying user''s AP over...')
        orig = arcpy.FeatureClassToFeatureClass_conversion(input_fc, fgdb + r'\OrigData', 'orig_AP')

        print_to_stdout('Adding unique ID field...')

        arcpy.AddField_management(orig, 'AP_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser AP ID')
        uid = 0
        with arcpy.da.UpdateCursor(orig, ['AP_ID_GeoAdd']) as ucur:
            for row in ucur:
                uid += 1
                row[0] = 'AP_{0}'.format(str(uid))
                ucur.updateRow(row)
        del(ucur, row)

        arcpy.AddField_management(nena_out, 'AP_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser AP ID')

        out_flds = []
        orig_flds = []
        for f in flds:
            if f[1] != '':
                orig_flds.append(f[1])
                out_flds.append(str(nena_flds[f[0]][0]))
        orig_flds.append('AP_ID_GeoAdd')
        out_flds.append('AP_ID_GeoAdd')
        orig_flds.append('SHAPE@')
        out_flds.append('SHAPE@')

        icur = arcpy.da.InsertCursor(nena_out, out_flds)
        with arcpy.da.SearchCursor(orig, orig_flds) as scur:
            for row in scur:
                icur.insertRow(row)
        del(icur, scur, row)

    else:
        print_to_stderr('Unacceptable value entered. Must be ''RCL'' or ''AP''')

    return(fgdb)

def migrateParcels(fgdb, parcel, parcel_flds, sr):

    if not arcpy.Exists(fgdb):
        print_to_stderr('GeoAnalyzer file geodatabase not found! What!?')

    orig = arcpy.FeatureClassToFeatureClass_conversion(parcel, fgdb + r'\OrigData', 'orig_Parcel')

    arcpy.AddField_management(orig, 'Parcel_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser Parcel ID')

    uid = 0
    with arcpy.da.UpdateCursor(orig, ['Parcel_ID_GeoAdd']) as ucur:
        for row in ucur:
            uid += 1
            row[0] = 'Parcel_{0}'.format(str(uid))
            ucur.updateRow(row)
    del(ucur, row)

    par_fld_types = {str(f.name):str(f.type) for f in arcpy.ListFields(orig)}

    if len(parcel_flds) > 1:

        flds = []

        flds.append(['AddNum_Pre', parcel_flds[0]])
        flds.append(['Add_Number', parcel_flds[1]])
        flds.append(['AddNum_Suf', parcel_flds[2]])
        flds.append(['St_PreDir', parcel_flds[3]])
        flds.append(['St_Name', parcel_flds[4]])
        flds.append(['St_PosTyp', parcel_flds[5]])
        flds.append(['St_PosDir', parcel_flds[6]])

        out_parcels = arcpy.CreateFeatureclass_management(fgdb + r'\GeoAnalyzerData', 'Parcels', 'POLYGON', spatial_reference=sr)

        out_flds = []
        orig_flds = []

        for n in flds:
            if n[1] != '':
                arcpy.AddField_management(out_parcels, n[0], par_fld_types[n[1]])
                out_flds.append(n[0])
                orig_flds.append(n[1])

        arcpy.AddField_management(out_parcels, 'Parcel_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser Parcel ID')

        orig_flds.append('Parcel_ID_GeoAdd')
        out_flds.append('Parcel_ID_GeoAdd')
        orig_flds.append('SHAPE@')
        out_flds.append('SHAPE@')

        icur = arcpy.da.InsertCursor(out_parcels, out_flds)
        with arcpy.da.SearchCursor(orig, orig_flds) as scur:
            for row in scur:
                icur.insertRow(row)
        del(icur, scur, row)       

    else:

        out_parcels = arcpy.CreateFeatureclass_management(fgdb + r'\GeoAnalyzerData', 'Parcels', 'POLYGON', spatial_reference=sr)

        arcpy.AddField_management(out_parcels, 'FullAdd', 'TEXT')
        arcpy.AddField_management(out_parcels, 'Parcel_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser Parcel ID')

        orig_flds = [parcel_flds[0], 'Parcel_ID_GeoAdd', 'SHAPE@']
        out_flds = ['FullAdd', 'Parcel_ID_GeoAdd', 'SHAPE@']

        icur = arcpy.da.InsertCursor(out_parcels, out_flds)
        with arcpy.da.SearchCursor(orig, orig_flds) as scur:
            for row in scur:
                icur.insertRow(row)
        del(icur, scur, row)

    print_to_stdout('Parcels added')

def migrateZip(fgdb, zipcode, zip_fld, sr):

    if not arcpy.Exists(fgdb):
        print_to_stderr('GeoAnalyzer file geodatabase not found! What!?')

    orig = arcpy.FeatureClassToFeatureClass_conversion(zipcode, fgdb + r'\OrigData', 'orig_Zipcodes')

    arcpy.AddField_management(orig, 'Zipcode_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser Zipcode ID')

    uid = 0
    with arcpy.da.UpdateCursor(orig, ['Zipcode_ID_GeoAdd']) as ucur:
        for row in ucur:
            uid += 1
            row[0] = 'Zip_{0}'.format(str(uid))
            ucur.updateRow(row)
    del(ucur, row)

    out_zips = arcpy.CreateFeatureclass_management(fgdb + r'\GeoAnalyzerData', 'Zipcodes', 'POLYGON', spatial_reference=sr)

    arcpy.AddField_management(out_zips, 'Post_Code', 'TEXT')
    arcpy.AddField_management(out_zips, 'Zipcode_ID_GeoAdd', 'TEXT', field_alias='GeoAddresser Zipcode ID')

    orig_flds = [zip_fld, 'Zipcode_ID_GeoAdd', 'SHAPE@']
    out_flds = ['Post_Code', 'Zipcode_ID_GeoAdd', 'SHAPE@']

    icur = arcpy.da.InsertCursor(out_zips, out_flds)
    with arcpy.da.SearchCursor(orig, orig_flds) as scur:
        for row in scur:
            icur.insertRow(row)
    del(icur, scur, row)

    print_to_stdout('Zipcodes added')

def migrateBoundaries(fgdb, bnds, sr):

    if not arcpy.Exists(fgdb):
        print_to_stderr('GeoAnalyzer file geodatabase not found! What!?')

    for bnd in bnds:

        name = arcpy.Describe(bnd).baseName
        if '.' in name:
            name = str(name.split('.')[-1])

        orig = arcpy.FeatureClassToFeatureClass_conversion(bnd, fgdb + r'\OrigData', 'orig_{}'.format(name))

        arcpy.AddField_management(orig, '{}_ID_GeoAdd'.format(name), 'TEXT', field_alias='GeoAddresser {} ID'.format(name))

        uid = 0
        with arcpy.da.UpdateCursor(orig, ['{}_ID_GeoAdd'.format(name)]) as ucur:
            for row in ucur:
                uid += 1
                row[0] = '{0}_{1}'.format(name, str(uid))
                ucur.updateRow(row)
        del(ucur, row)

        out_bnd = arcpy.CreateFeatureclass_management(fgdb + r'\GeoAnalyzerData', name, 'POLYGON', spatial_reference=sr)

        arcpy.AddField_management(out_bnd, '{}_ID_GeoAdd'.format(name), 'TEXT', field_alias='GeoAddresser {} ID'.format(name))

        orig_flds = ['{}_ID_GeoAdd'.format(name), 'SHAPE@']
        out_flds = ['{}_ID_GeoAdd'.format(name), 'SHAPE@']

        icur = arcpy.da.InsertCursor(out_bnd, out_flds)
        with arcpy.da.SearchCursor(orig, orig_flds) as scur:
            for row in scur:
                icur.insertRow(row)
        del(icur, scur, row)

        print_to_stdout('{} added'.format(name))



if __name__ == '__main__':

    try:

        ## -----------------------------------------------------------------------------------
        # LOG
        ## -----------------------------------------------------------------------------------

        current = datetime.today()
        logfile = (path.abspath(path.join(path.dirname(__file__), '..', r'logs\RCL_MigrationPrep_log_{0}_{1}.txt'.format(current.month, current.year))))
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S')

        ## -----------------------------------------------------------------------------------
        # INPUTS
        ## -----------------------------------------------------------------------------------

        print_to_stdout('Constructing dictionaries and lists from json...')

        json_path = (path.abspath(path.join(path.dirname(__file__), '.', r'nena_required_values.json')))
        print(json_path)
        # json_path = r"C:\Users\NikitaSinha\Downloads\forDev\forDev\supp_data\nena_required_values.json"

        text = open(json_path).read()
        json_array = json.loads(text)

        mco_dict = json_array['mco_dict'][0]
        nena_dir = json_array['nena_dir']
        nena_sttypes = json_array['nena_sttypes']
        nena_parity = json_array['nena_parity']
        nena_oneway = json_array['nena_oneway']
        nena_mtfcc = json_array['nena_mtfcc']

        # nena_fgdb = path.abspath(path.join(path.dirname(__file__), '..', r'supp_data\NENA_schema.fgdb'))
        nena_fgdb = r'C:\data\gtg-data\projects\_geoaddresser-tool\GTG-scripts\NENA_schema.gdb'

        # string of path to rcl
        input_rcl = arcpy.GetParameterAsText(0) #r'D:\Kissimmee.gdb\parks'
        input_rcl_flds = ast.literal_eval(arcpy.GetParameterAsText(1)) #ast.literal_eval("[['Discrepancy Agency ID','ID'],['Date Updated','Shape']]")

        input_ap = arcpy.GetParameterAsText(2)
        input_ap_flds = ast.literal_eval(arcpy.GetParameterAsText(3))

        parcels = arcpy.GetParameterAsText(4)
        single_add_fld = arcpy.GetParameterAsText(5) #boolean
        fulladd = arcpy.GetParameterAsText(6)
        parcel_addpre = arcpy.GetParameterAsText(7)
        parcel_addnum = arcpy.GetParameterAsText(8)
        parcel_addsuf = arcpy.GetParameterAsText(9)
        parcel_predir = arcpy.GetParameterAsText(10)
        parcel_stname = arcpy.GetParameterAsText(11)
        parcel_type = arcpy.GetParameterAsText(12)
        parcel_posdir = arcpy.GetParameterAsText(13) 

        if parcels != '':
            if single_add_fld == 'True':
                parcel_flds = [fulladd]
            elif single_add_fld == 'False':
                parcel_flds = [parcel_addpre, parcel_addnum, parcel_addsuf, parcel_predir, 
                                parcel_stname, parcel_type, parcel_posdir] 
            else:
                print_to_stderr('Must provide site address as a single field or as multiple fields!')  

        zipcodes = arcpy.GetParameterAsText(14)
        zip_fld = arcpy.GetParameterAsText(15)

        supp_bnds = ast.literal_eval(arcpy.GetParameterAsText(16))

        migrate_bool = arcpy.GetParameterAsText(17)

        # need to create validation check on sr, otherwise if all same, populate with arcpy.Describe(input_rcl).spatialReference
        # all_sr = []
        # for i in ([input_rcl, input_ap, parcels, zipcodes] + supp_bnds):
        #     i_sr = (arcpy.Describe(i).spatialReference).factoryCode
        #     all_sr.append(i_sr)
        # if len(list(set(all_sr))) != 1:
        #     # Raise the alarms! Produce list of SR options (inputs, and all)
        #     # force user to choose one SR before running anything. 
        #     # that sr input will be fed into the sr variable 
        # else:
        #     sr = arcpy.Describe(input_rcl).spatialReference
        # sr = arcpy.Describe(input_rcl).spatialReference.factoryCode #arcpy.GetParameterAsText(5)
        sr = arcpy.Describe(input_rcl).spatialReference.factoryCode #arcpy.GetParameterAsText(5)

        ## -----------------------------------------------------------------------------------
        ## OUTPUTS
        ## -----------------------------------------------------------------------------------

        output_folder = arcpy.GetParameterAsText(18) #r'C:\Users\NikitaSinha\Downloads\forDev\forDev\output'
        output_rcl_csv = arcpy.GetParameterAsText(19) #r'C:\Users\NikitaSinha\Downloads\forDev\forDev\output\output.csv'
        output_rcl_csv = output_folder +r'\{}'.format(output_rcl_csv)
        output_ap_csv = arcpy.GetParameterAsText(20)
        output_ap_csv = output_folder +r'\{}'.format(output_ap_csv)
        

        timestamp = datetime.now().strftime('%m%d%Y')
        fgdb_name = 'GeoAnalyzer_{0}.gdb'.format(timestamp)
        out_fgdb = output_folder + r'\{}'.format(fgdb_name)

        ## -----------------------------------------------------------------------------------
        # MODULES
        ## -----------------------------------------------------------------------------------

        if input_rcl != '':
            print_to_stdout("Creating migration prep CSV for RCL...") 
            finalnotes = createMigrationCSV(input_rcl, input_rcl_flds, 'RCL', output_rcl_csv)
            if ('Convert' not in finalnotes and 'length' not in finalnotes) and migrate_bool == 'True':
                print_to_stdout('CSV looks good! Migrating RCL to working FGDB...')
                migrateToFGDB(input_rcl, input_rcl_flds, out_fgdb, nena_fgdb, output_folder, 'RCL', sr)
            else:
                print_to_stdout('RCL needs cleaning up before migration can occur...')
        if input_ap != '':
            print_to_stdout("Creating migration prep CSV for AP...") 
            finalnotes = createMigrationCSV(input_ap, input_ap_flds, 'AP', output_ap_csv)
            if ('Convert' not in finalnotes and 'length' not in finalnotes) and migrate_bool == 'True':
                print_to_stdout('CSV looks good! Migrating AP to working FGDB...')
                migrateToFGDB(input_ap, input_ap_flds, out_fgdb, nena_fgdb, output_folder, 'AP', sr)
            else:
                print_to_stdout('AP needs cleaning up before migration can occur...')
        if migrate_bool == 'True' and arcpy.Exists(out_fgdb):
            if parcels != '':
                print_to_stdout('Migrating parcels...')
                migrateParcels(out_fgdb, parcels, parcel_flds, sr)
            if zipcodes != '':
                print_to_stdout('Migrating zipcodes...')
                migrateZip(out_fgdb, zipcodes, zip_fld, sr)
            if supp_bnds != '':
                print_to_stdout('Migrating supplemental boundaries...')
                migrateBoundaries(out_fgdb, supp_bnds, sr)

        print_to_stdout("Success! \n ------------------------------------ \n\n") 

    except Exception as e:        
        logging.error("EXCEPTION OCCURRED", exc_info=True)
        print_to_stderr("Quitting! \n ------------------------------------ \n\n")

