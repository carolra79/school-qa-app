# Code Documentation and Commenting Rules

## Purpose
Ensure consistent, clear documentation and comments across the codebase for maintainability and knowledge transfer.

## Code Comments

### Function Documentation
- Every function must have a docstring explaining its purpose
- Include parameter types and return values where applicable
- Use triple quotes for Python docstrings

```python
def upload_to_s3(file):
    """Upload file to S3 bucket
    
    Args:
        file: File object to upload
        
    Returns:
        tuple: (success_bool, file_key_string)
    """
```

### Inline Comments
- Add comments for complex logic or business rules
- Explain WHY, not just WHAT the code does
- Keep comments concise and relevant

### Configuration Comments
- Document all environment variables and their purpose
- Explain configuration parameters in JSON/YAML files

## README Requirements

### Must Include
- **Purpose**: Clear description of what the application does
- **Features**: Key functionality list
- **Dependencies**: Required packages, AWS services, Python version
- **Setup**: Installation and configuration steps
- **Usage**: How to run the application
- **Environment Variables**: Required variables and their values
- **AWS Services**: List of AWS services used and required permissions

### Structure Example
```markdown
# Project Name
Brief description

## Features
- Feature 1
- Feature 2

## Dependencies
- Python 3.x
- AWS Bedrock
- Streamlit

## Setup
1. Install requirements
2. Configure AWS credentials
3. Set environment variables

## Usage
How to run the app

## Environment Variables
- VAR_NAME: Description
```

## File Headers
- Include purpose comment at top of each Python file
- List key dependencies used in the file
- Add author/maintainer information if relevant

## AWS-Specific Documentation
- Document IAM permissions required
- Explain AWS service configurations
- Include region and resource naming conventions
- Document cost implications of AWS services used

## Maintenance
- Update documentation when code changes
- Keep README current with actual functionality
- Remove outdated comments and documentation
