import os
import json
import re

def parse_markdown_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split by course headers (e.g., ACCT 110)
    # The pattern looks for Course Code followed by Title and Credit Hours
    # Example: ACCT 110\n Introduction to Financial Accounting3 - 0 - 3
    # Followed by a separator line
    
    # regex to find courses
    # Group 1: Code
    # Group 2: Title
    # Group 3: Lec - Lab - Cr
    # Group 4: Description (everything until the next course or end of important content)
    
    courses = []
    
    # Split the content into blocks using the separator line
    # Each course block starts some lines before the separator
    blocks = re.split(r'-{10,}', content)
    
    for i in range(len(blocks) - 1):
        prev_block_lines = blocks[i].strip().split('\n')
        current_block_lines = blocks[i+1].strip().split('\n')
        
        if len(prev_block_lines) < 2:
            continue
            
        # The course code and title are usually in the last two lines of the previous block
        # line -2: Code
        # line -1: Title + Credits
        
        line_code = prev_block_lines[-2].strip()
        line_title_credits = prev_block_lines[-1].strip()
        
        # Regex for credits at the end of the line: "3 - 0 - 3" or similar
        credit_match = re.search(r'(\d+)\s*-\s*(\d+)\s*-\s*(\d+)$', line_title_credits)
        
        if credit_match:
            title = line_title_credits[:credit_match.start()].strip()
            lec = int(credit_match.group(1))
            lab = int(credit_match.group(2))
            credits = int(credit_match.group(3))
        else:
            title = line_title_credits
            lec = 0
            lab = 0
            credits = 0
            
        # Description is the text in the next block until a pre-requisite or the next course stuff
        description_lines = []
        prerequisites = ""
        
        for line in current_block_lines:
            if "**Pre-Requisites:**" in line:
                prerequisites = line.replace("**Pre-Requisites:**", "").strip()
                break
            if "Prerequisite:" in line:
                prerequisites = line.replace("Prerequisite:", "").strip()
                break
            # If we reach what looks like a new course code, stop (though split should handle this)
            if re.match(r'^[A-Z]+\s+\d+$', line.strip()):
                break
            description_lines.append(line)
            
        description = "\n".join(description_lines).strip()
        
        courses.append({
            "code": line_code,
            "title": title,
            "lecture_hours": lec,
            "lab_hours": lab,
            "credits": credits,
            "description": description,
            "prerequisites": prerequisites
        })
        
    return courses

def main():
    raw_data_dir = 'raw_undergraduate_data'
    output_file = 'processed_undergraduate_courses.json'
    all_courses = []
    
    if not os.path.exists(raw_data_dir):
        print("Raw data directory not found.")
        return
        
    files = sorted([f for f in os.listdir(raw_data_dir) if f.endswith('.md')])
    
    for file_name in files:
        print(f"Processing: {file_name}")
        dept_courses = parse_markdown_file(os.path.join(raw_data_dir, file_name))
        all_courses.extend(dept_courses)
        
    with open(output_file, 'w') as f:
        json.dump(all_courses, f, indent=2)
        
    print(f"Total courses processed: {len(all_courses)}")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    main()
