"""
AWS Lambda entry point for MemoryMesh. Wraps the FastAPI app with Mangum.

Deploy notes:
  1. pip install -r requirements.txt -t package/
  2. pip install mangum -t package/
  3. cp -r app package/
  4. cp lambda/lambda_handler.py package/
  5. cd package && zip -r ../memorymesh_lambda.zip . && cd .. 
  6. Create Lambda function (Python 3.12), upload memorymesh_lambda.zip
  7. Handler: lambda_handler.handler
  8. Set env vars (DATABASE_URL, AWS_REGION, USE_BEDROCK, etc.) 
  9. Enable a Function URL  
"""  
from mangum import Mangum
from app.main import app 
 
handler = Mangum(app)
 

