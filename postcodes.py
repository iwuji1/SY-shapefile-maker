import pandas as pd
import geopandas as gpd
import zipfile
import os

def process_data(input_path):

    shapefile_folder = "outputs"
    for fname in os.listdir(shapefile_folder):
        fpath = os.path.join(shapefile_folder, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)
    
    # 1. Load Excel
    # 2. Clean it
    # 3. Merge with GeoJSON
    # 4. Output Shapefile

    print("Does /tmp exist?", os.path.exists("/tmp"))
    print("Writable?", os.access("/tmp", os.W_OK))



    df_ref = pd.read_csv(input_path)
    geojson_path = "uploads/MSOA_Boundaries_v2.geojson"
    gdf = gpd.read_file(geojson_path)

    #Filtering for South Yorkshir
    SY_df = df_ref[df_ref['ITL2_name'] == 'South Yorkshire']

    print("Columns in SY_df:", SY_df.columns.tolist())
    SY_df.columns = SY_df.columns.str.strip()  # Remove whitespace
    SY_df_filtered = SY_df[['LSOA_name', 'MSOA_current', 'MSOA_name', 'POLAR4_quintile', 'POLAR3_quintile', 'TUNDRA_MSOA_quintile', 'TUNDRA_LSOA_quintile', 'Adult_HE_2011_quintile','Gaps_GCSE_quintile','Gaps_GCSE_Ethnicity_quintile']]
    
    #Replace the Rotherham 022 and 024 with Rotherham 034 and 
    #Define the new MSOA Code
    new_msoa_code = 'E02007002'

    #Find the row where 'LSOA name' contains "Rotherham 022 & 024
    mask = SY_df_filtered['LSOA_name'].str.contains('Rotherham 022', na=False)
    mask2 = SY_df_filtered['LSOA_name'].str.contains('Rotherham 024', na=False)

    # Update LSOA name to replace 'Rotherham 022' with 'Rotherham 
    SY_df_filtered.loc[mask, 'LSOA_name'] = SY_df_filtered.loc[mask, 'LSOA_name'].str.replace('Rotherham 022', 'Rotherham 034')
    SY_df_filtered.loc[mask2, 'LSOA_name'] = SY_df_filtered.loc[mask2, 'LSOA_name'].str.replace('Rotherham 024', 'Rotherham 034')

    # Update MSOA current
    SY_df_filtered.loc[mask, 'MSOA current'] = new_msoa_code
    SY_df_filtered.loc[mask2, 'MSOA current'] = new_msoa_code

    # Rename Column to match shapefile
    SY_df_filtered = SY_df_filtered.rename(columns={"MSOA current": "MSOA21CD"})

    #Merge and final file
    merged_gdf = gdf.merge(SY_df_filtered, on="MSOA21CD", how="left")
    districts = ["Barnsley", "Doncaster", "Rotherham", "Sheffield"]
    pattern = "|".join(districts)
    south_yorkshire_df = merged_gdf[merged_gdf["LSOA_name"].str.contains(pattern, case=False, na=False)]
    shapefile_path = os.path.join(shapefile_folder, "South_Yorkshire_shape.shp")
    shapefile_base = "South_Yorkshire_shape"
    zip_path = os.path.join(shapefile_folder, f"{shapefile_base}.zip")
    print("Saving to:", shapefile_folder)
    print("Do I have write permission?", os.access(shapefile_folder, os.W_OK))

    print("shapefile_folder:", shapefile_folder)
    print("shapefile_path:", shapefile_path)
    print("Folder exists:", os.path.exists(shapefile_folder))
    print("Folder permissions:", oct(os.stat(shapefile_folder).st_mode))
    print("Write permission:", os.access(shapefile_folder, os.W_OK))

    #check_south_yorkshire_df = sanitize_column_names(south_yorkshire_df)
    south_yorkshire_df.to_file(shapefile_path, driver='ESRI Shapefile')

    # List all files with the base name
    files_to_zip = [
        fname for fname in os.listdir(shapefile_folder)
        if fname.startswith(shapefile_base)
    ]
    
    # Zip all shapefile component
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for fname in files_to_zip:
            fpath = os.path.join(shapefile_folder, fname)
            zipf.write(fpath, arcname=fname)
    print(f"Zipped files: {files_to_zip}")
