import pandas as pd
import logging
import os
import sys
from datetime import datetime
from simulation_config import BATCH_DATA_PATH

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def generate_summary(sim_date_str):
    """Generates a summary file for a given simulation day."""
    admissions_file = f"{BATCH_DATA_PATH}/admissions_{sim_date_str}.csv"
    summary_file = f"{BATCH_DATA_PATH}/summary_{sim_date_str}.txt"

    try:
        admissions_df = pd.read_csv(admissions_file)
        num_admissions = len(admissions_df)
        
        summary_content = f"""
        Hospital Summary for: {sim_date_str}
        =======================================
        Generated at: {datetime.now().isoformat()}
        
        Total Admissions: {num_admissions}
        
        Top 5 Conditions:
        {admissions_df['condition'].value_counts().nlargest(5).to_string()}
        """
        
        with open(summary_file, "w") as f:
            f.write(summary_content)
        
        logging.info(f"Generated hospital summary: {summary_file}")

    except FileNotFoundError:
        logging.warning(f"Admissions file not found for summary: {admissions_file}")
    except Exception as e:
        logging.error(f"Failed to generate summary: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_summary(sys.argv[1])
    else:
        logging.error("No simulation date provided to generate_hospital_summary.py.")
