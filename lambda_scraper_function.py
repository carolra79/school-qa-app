import boto3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def lambda_handler(event, context):
    # Configuration with your specific bucket and folder
    website_url = "https://st-marys.richmond.sch.uk/"
    s3_bucket = "school-qa-docs-v2"
    s3_folder = "school-docs"
    
    # Get current date for filename
    current_date = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"st_marys_school_{current_date}.txt"
    
    try:
        # Fetch website content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(website_url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text from main content areas
        content_areas = soup.find_all(['article', 'section', 'div', 'main'])
        
        # Compile text content
        content = f"St Mary's CE Primary School Website Content\nURL: {website_url}\nExtracted on: {current_date}\n\n"
        
        # Extract page title and add to content
        if soup.title:
            content += f"Page Title: {soup.title.string.strip()}\n\n"
        
        # Process main content
        for area in content_areas:
            # Get all text elements
            elements = area.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'a'])
            for element in elements:
                text = element.get_text().strip()
                if text:  # Only add non-empty text
                    content += text + "\n\n"
        
        # Also grab navigation links which often contain important school information
        nav_links = soup.find_all('a')
        content += "Navigation Links:\n"
        for link in nav_links:
            if link.get('href') and link.text.strip():
                content += f"- {link.text.strip()}: {link.get('href')}\n"
        
        # Upload to S3 in your specific folder
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=f"{s3_folder}/{output_filename}",
            Body=content,
            ContentType='text/plain'
        )
        
        return {
            'statusCode': 200,
            'body': f'Successfully scraped St Mary\'s School website and uploaded to S3 bucket {s3_bucket} in folder {s3_folder} as {output_filename}'
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error processing website: {str(e)}'
        }


