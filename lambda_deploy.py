import zipfile
import os

def create_lambda_package():
    """Create deployment package for Lambda"""
    
    files_to_include = [
        'agentcore_main.py',
        'config.py'
    ]
    
    with zipfile.ZipFile('agentcore-lambda.zip', 'w') as zipf:
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file)
                print(f"Added {file}")
    
    print("Created agentcore-lambda.zip")
    print("\nNext steps:")
    print("1. Upload this zip to Lambda")
    print("2. Set handler to: agentcore_main.lambda_handler")
    print("3. Add environment variables from config.py")
    print("4. Create API Gateway trigger")

if __name__ == "__main__":
    create_lambda_package()
