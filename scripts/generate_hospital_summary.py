import pandas as pd
import logging
import os
import sys
from datetime import datetime
import glob

# Import shared configuration
from simulation_config import BATCH_DATA_PATH, STREAM_DATA_PATH

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def read_and_concat_session_files(pattern):
    """Finds all session files matching a pattern and concatenates them into a single dataframe."""
    files = glob.glob(pattern)
    if not files:
        return pd.DataFrame()
    
    df_list = [pd.read_csv(f) for f in files]
    return pd.concat(df_list, ignore_index=True)

def generate_comprehensive_summary(sim_date_str):
    """
    Generates a comprehensive summary report for a given simulation day by reading all
    relevant daily output files.
    """
    
    # --- Load all daily data files ---
    admissions_file = f"{BATCH_DATA_PATH}/admissions_{sim_date_str}.csv"
    denied_file = f"{BATCH_DATA_PATH}/denied_admissions_{sim_date_str}.csv"
    outpatient_file = f"{BATCH_DATA_PATH}/outpatient_attendances_{sim_date_str}.csv"
    visitors_file = f"{BATCH_DATA_PATH}/daily_visitors_{sim_date_str}.csv"
    
    # Use glob to find all session files for transport and transfers
    transport_pattern = f"{STREAM_DATA_PATH}/hospital_emergency_transport_{sim_date_str}_session_*.csv"
    transfers_pattern = f"{STREAM_DATA_PATH}/hospital_transfers_{sim_date_str}_session_*.csv"

    try:
        visitors_df = pd.read_csv(visitors_file)
        admissions_df = pd.read_csv(admissions_file) if os.path.exists(admissions_file) else pd.DataFrame()
        denied_df = pd.read_csv(denied_file) if os.path.exists(denied_file) else pd.DataFrame()
        outpatient_df = pd.read_csv(outpatient_file) if os.path.exists(outpatient_file) else pd.DataFrame()
        
        transport_df = read_and_concat_session_files(transport_pattern)
        transfers_df = read_and_concat_session_files(transfers_pattern)

    except FileNotFoundError as e:
        logging.warning(f"Could not generate full summary for {sim_date_str}, missing a key input file: {e}")
        return

    # --- Generate the Summary Content ---
    summary_content = f"""
    Hospital Daily Operations Summary for: {sim_date_str}
    =======================================================
    Generated at: {datetime.now().isoformat()}

    --- Patient Flow ---
    Total Patient Visits: {len(visitors_df)}
    - Inpatient Admissions: {len(admissions_df)}
    - Outpatient Attendances: {len(outpatient_df)}
    - Inpatients Denied (Capacity): {len(denied_df)}

    --- Transport & Transfers ---
    Total Emergency Transport Events: {len(transport_df)}
    Total Patient Transfers: {len(transfers_df)}
    """

    if not admissions_df.empty:
        summary_content += "\n\n--- Inpatient Details ---\n"
        summary_content += "\nAdmissions by Department:\n" + admissions_df['Department'].value_counts().to_string()
        summary_content += "\n\nAdmitting Doctor Workload:\n" + admissions_df['Admitting_Doctor'].value_counts().to_string()
        summary_content += "\n\nAdmitting Nurse Workload:\n" + admissions_df['Admitting_Nurse'].value_counts().to_string()

    if not transport_df.empty:
        summary_content += "\n\n--- Transport Details ---\n"
        summary_content += "\nTransport Types:\n" + transport_df['Transport_Type'].value_counts().to_string()
        
        ambulance_cases = transport_df[transport_df['Transport_Type'] == 'Ambulance']
        if not ambulance_cases.empty:
            summary_content += "\n\nAmbulance Cases by Severity:\n" + ambulance_cases['Severity'].value_counts().sort_index().to_string()

    if not transfers_df.empty:
        summary_content += "\n\n--- Transfer Details ---\n"
        summary_content += "\nTransfers by Destination:\n" + transfers_df['Transfer_To'].value_counts().to_string()
        summary_content += "\n\nTransfers by Reason:\n" + transfers_df['Transfer_Reason'].value_counts().to_string()

    # --- Save the final summary file ---
    summary_file = f"{BATCH_DATA_PATH}/hospital_summary_{sim_date_str}.txt"
    with open(summary_file, 'w') as f:
        f.write(summary_content)
    
    logging.info(f"Generated comprehensive hospital summary: {summary_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_comprehensive_summary(sys.argv[1])
    else:
        logging.error("No simulation date provided to generate_hospital_summary.py.")
