import pandas as pd
import os

csv_path = "/home/shared_dir/data/SQL/departments.csv"

# User provided data
# Department Name on CSV (Approx) -> Link
# I will create a mapping based on my best understanding of the CSV content and user request.

mapping = {
    # Group 1
    "Aerospace Engineering": "https://ae.kfupm.edu.sa/",
    "Control and Instrumentation Engineering": "https://cie.kfupm.edu.sa/",
    "Electrical Engineering": "https://ee.kfupm.edu.sa/",
    "Mechanical Engineering": "https://me.kfupm.edu.sa/",
    "Physics": "https://physics.kfupm.edu.sa/",
    
    # Group 2
    "Computer Engineering": "https://coe.kfupm.edu.sa/",
    "Industrial and Systems Engineering": "https://ise.kfupm.edu.sa/",
    "Information and Computer Science": "https://ics.kfupm.edu.sa/", # User: Information & Computer Science
    "Mathematics": "https://math.kfupm.edu.sa/",
    
    # Group 3
    # "Center for Integrative Petroleum Research": "https://cpg.kfupm.edu.sa/cipr/", # Not in CSV?
    "Geosciences": "https://cpg.kfupm.edu.sa/academics/departments/department-of-geosciences/",
    "Petroleum Engineering": "https://cpg.kfupm.edu.sa/academics/departments/department-of-petroleum-engineering/",
    
    # Group 4
    "Bioengineering": "https://bioe.kfupm.edu.sa/",
    "Chemical Engineering": "https://che.kfupm.edu.sa/",
    "Chemistry": "https://chemistry.kfupm.edu.sa/",
    "Material Science and Engineering": "https://mse.kfupm.edu.sa/", # CSV has Science (singular) usually
    
    # Group 5
    "Architectural Engineering": "https://aecm.kfupm.edu.sa/",
    "Construction Engineering Management": "https://aecm.kfupm.edu.sa/", # Mapped from combined name
    "Architecture": "https://acd.kfupm.edu.sa/",
    "Civil Engineering": "https://ce.kfupm.edu.sa/",
    "Environmental Engineering": "https://ce.kfupm.edu.sa/", # Mapped from combined name
    "Information Technology and Digital Design": "https://itd.kfupm.edu.sa/", # User: Integrated Design
    
    # Group 6
    "Accounting": "https://kbs.kfupm.edu.sa/academics/accounting-and-finance/",
    "Finance": "https://kbs.kfupm.edu.sa/academics/accounting-and-finance/",
    # "Global Studies": "https://kbs.kfupm.edu.sa/academics/global-studies/", # Not explicitly found, maybe General Studies?
    "General Studies": "https://kbs.kfupm.edu.sa/academics/global-studies/", # Assumption based on GS shortcut and link context
    "Management Information Systems": "https://kbs.kfupm.edu.sa/academics/information-systems-and-operations-management/",
    "Operations Management": "https://kbs.kfupm.edu.sa/academics/information-systems-and-operations-management/",
    "Management and Marketing": "https://kbs.kfupm.edu.sa/academics/management-marketing/",
    "Management": "https://kbs.kfupm.edu.sa/academics/management-marketing/",
    "Marketing": "https://kbs.kfupm.edu.sa/academics/management-marketing/",
    
    # Group 7
    "English": "https://eld.kfupm.edu.sa/",
    "Islamic and Arabic Studies": "https://ias.kfupm.edu.sa/",
    "Physical Education": "https://pe.kfupm.edu.sa/",
    # "Prep-Year": "https://pyp.kfupm.edu.sa/" # Not found in CSV
}

# Add partial match or special cases if needed
# For now, strict matching on keys.

def update_csv():
    # Read CSV
    # Using python's built-in csv module to avoid pandas issues with header logic if strictly needed, 
    # but pandas is easier. load_data_sqlite uses pandas.
    
    df = pd.read_csv(csv_path)
    
    # Add link column if not exists
    if 'link' not in df.columns:
        df['link'] = None
    
    # Iterate and update
    for index, row in df.iterrows():
        name = row['name']
        
        # Exact match
        if name in mapping:
            df.at[index, 'link'] = mapping[name]
        
        # Fuzzy / Manual fixes
        # Check for "Global Studies" matching "General Studies" if strict match failed?
        # Checked in mapping dict.
        
        # Check for "Material Sciences" vs "Material Science"
        if name == "Material Science and Engineering" and name not in mapping:
             df.at[index, 'link'] = "https://mse.kfupm.edu.sa/"
             
    # Save back
    df.to_csv(csv_path, index=False)
    print("Updated departments.csv with links.")

if __name__ == "__main__":
    update_csv()
