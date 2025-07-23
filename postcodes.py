import pandas as pd
import geopandas as gpd
import zipfile
import os

def process_data(input_path):
    shapefile_folder = "/tmp/outputs"
    shapefile_base = "South_Yorkshire_shape"
    shapefile_path = os.path.join(shapefile_folder, f"{shapefile_base}.shp")
    zip_path = os.path.join(shapefile_folder, f"{shapefile_base}.zip")

    # Ensure /tmp/outputs exists
    os.makedirs(shapefile_folder, exist_ok=True)

    # Clear old files
    for fname in os.listdir(shapefile_folder):
        fpath = os.path.join(shapefile_folder, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)

    print("Does /tmp exist?", os.path.exists("/tmp"))
    print("Writable?", os.access("/tmp", os.W_OK))

    # Step 1: Load data
    df_ref = pd.read_csv(input_path)
    geojson_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "MSOA_Boundaries_v2.geojson")
    gdf = gpd.read_file(geojson_path)

    # Step 2: Filter for South Yorkshire
    df_ref.columns = df_ref.columns.str.strip()
    if "ITL2_name" not in df_ref.columns:
        raise ValueError("Missing 'ITL2_name' column in CSV.")

    SY_df = df_ref[df_ref['ITL2_name'] == 'South Yorkshire']

    # Expected columns
    required_columns = [
        'LSOA_name', 'MSOA_current', 'MSOA_name',
        'POLAR4_quintile', 'POLAR3_quintile', 'TUNDRA_MSOA_quintile',
        'TUNDRA_LSOA_quintile', 'Adult_HE_2011_quintile',
        'Gaps_GCSE_quintile', 'Gaps_GCSE_Ethnicity_quintile'
    ]
    missing_cols = [col for col in required_columns if col not in SY_df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in input file: {missing_cols}")

    SY_df_filtered = SY_df[required_columns]

    # Step 3: Fix known MSOA issues (Rotherham 022/024)
    new_msoa_code = 'E02007002'
    for target in ['Rotherham 022', 'Rotherham 024']:
        mask = SY_df_filtered['LSOA_name'].str.contains(target, na=False)
        SY_df_filtered.loc[mask, 'LSOA_name'] = SY_df_filtered.loc[mask, 'LSOA_name'].str.replace(target, 'Rotherham 034')
        SY_df_filtered.loc[mask, 'MSOA_current'] = new_msoa_code

    # Step 4: Merge with GeoJSON
    SY_df_filtered = SY_df_filtered.rename(columns={'MSOA_current': 'MSOA21CD'})
    merged_gdf = gdf.merge(SY_df_filtered, on="MSOA21CD", how="left")

    # Step 5: Further filter by district (just in case)
    districts = ["Barnsley", "Doncaster", "Rotherham", "Sheffield"]
    pattern = "|".join(districts)
    south_yorkshire_df = merged_gdf[merged_gdf["LSOA_name"].str.contains(pattern, case=False, na=False)]

    # Step 6: Save as shapefile
    print("Saving shapefile to:", shapefile_path)
    south_yorkshire_df.to_file(shapefile_path, driver="ESRI Shapefile")

    # Step 7: Zip all shapefile components
    files_to_zip = [fname for fname in os.listdir(shapefile_folder) if fname.startswith(shapefile_base)]
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for fname in files_to_zip:
            zipf.write(os.path.join(shapefile_folder, fname), arcname=fname)

    print(f"Zipped files: {files_to_zip}")
    return zip_path