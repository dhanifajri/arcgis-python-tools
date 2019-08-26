# -*- coding: utf-8 -*-

import arcpy
import ntpath

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "WKT Tools"
        self.alias = "WKT"

        # List of tool classes associated with this toolbox
        self.tools = [WKTtoFeature]


class WKTtoFeature(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "WKT to Feature"
        self.description = "Convert file that contains WKT coordinate to feature class"
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""

        # Input File Parameter

        in_file = arcpy.Parameter(
            displayName="Input File",
            name="in_file",
            direction="Input",
            datatype="DETextFile",
            parameterType="Required"
        )

        # WKT Field Parameter

        wkt_field = arcpy.Parameter(
            displayName="WKT Field",
            name="wkt_field",
            direction="Input",
            datatype="Field",
            parameterType="Required",
        )

        wkt_field.parameterDependencies = [in_file.name]

        #Choose fields to be imported

        imported_fields = arcpy.Parameter(
            displayName="Imported Fields",
            name="imported_fields",
            direction="Input",
            datatype="Field",
            parameterType="Required",
            multiValue=True
        )

        imported_fields.parameterDependencies = [in_file.name]

        # Choose a spatial reference

        sr = arcpy.Parameter(
            displayName="Spatial Reference",
            name="sr",
            direction="Input",
            datatype="GPSpatialReference",
            parameterType="Required"
        )

        out_feature = arcpy.Parameter(
            displayName="Out Feature",
            name="out_feature",
            direction="Output",
            datatype="DEFeatureClass",
            parameterType="Required"
        )

        out_geom = arcpy.Parameter(
            displayName="Feature Type",
            name="out_geom",
            direction="Input",
            datatype="GPString",
            parameterType="Required"
        )

        out_geom.filter.type = "ValueList"
        out_geom.filter.list = ["POINT", "POLYLINE", "POLYGON"]

        params = [in_file, wkt_field, imported_fields, sr, out_feature, out_geom]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_file = parameters[0].valueAsText
        geom_field = parameters[1].valueAsText
        imported_fields = parameters[2].values
        sr = parameters[3].value
        out_feature = parameters[4].valueAsText
        in_fieldlist = arcpy.ListFields(in_file)
        in_fieldsname = []
        imported_fields_name = []
        out_basename = ntpath.basename(out_feature)
        out_dirname = ntpath.dirname(out_feature)
        out_geom = parameters[5].valueAsText


        # Create a feature class

        arcpy.CreateFeatureclass_management(out_dirname, out_name=out_basename, geometry_type=out_geom, spatial_reference=sr)


        # Add Field to the output

        for field in imported_fields:
            imported_fields_name.append(field.value)

            # Scanning fields

            for field in in_fieldlist:
                in_fieldsname.append(field.name)
                if field.name in imported_fields_name:
                    arcpy.AddField_management(out_feature, field.name, field.type)



        # Populate feature

        with arcpy.da.SearchCursor(in_file,[in_fieldsname[in_fieldsname.index(geom_field)]] + imported_fields_name) as scursor:
            with arcpy.da.InsertCursor(out_feature, ['SHAPE@'] + imported_fields_name) as icursor:
                fail = []
                for row in scursor:
                    try:
                        row = list(row)
                        newrow = arcpy.FromWKT(row[0], sr)
                        icursor.insertRow(tuple([newrow] + row[1:]))
                    except RuntimeError:
                        print(row[0])
                        fail.append(row[1])
                messages.addMessage(f"{len(fail)} features invalid")
