import os
import re
from oxylabs_ai_studio.apps.ai_scraper import AiScraper

def get_unique_codes(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    unique_codes = set()
    for line in lines:
        # Extract the alphabetical part (department code)
        match = re.match(r'^([A-Z]+)', line.strip())
        if match:
            unique_codes.add(match.group(1))
    
    return sorted(list(unique_codes))

def scrape_department(code, scraper):
    url = f"https://bulletin.kfupm.edu.sa/course-details?subject_code={code}&level=Undergraduate"
    print(f"Scraping: {url}")
    
    payload = {
        "url": url,
        "output_format": "markdown",
        "render_javascript": "auto"
    }
    
    try:
        result = scraper.scrape(**payload)
        return result.data
    except Exception as e:
        print(f"Error scraping {code}: {e}")
        return None

def main():
    course_codes_file = 'course_codes.txt'
    raw_data_dir = 'raw_undergraduate_data'
    
    if not os.path.exists(raw_data_dir):
        os.makedirs(raw_data_dir)
    
    unique_codes = get_unique_codes(course_codes_file)
    print(f"Found {len(unique_codes)} unique department codes.")
    
    # API key provided by user
    scraper = AiScraper(api_key="zqzk1KlGxb4Gyua5EX8b42mlNyJSBWez6gL9NeMI")
    
    for code in unique_codes:
        markdown_content = scrape_department(code, scraper)
        if markdown_content:
            file_name = f"{code}_undergraduate.md"
            with open(os.path.join(raw_data_dir, file_name), 'w') as f:
                f.write(markdown_content)
            print(f"Saved: {file_name}")

if __name__ == "__main__":
    main()
