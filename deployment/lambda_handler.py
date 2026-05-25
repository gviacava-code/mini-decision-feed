"""
AWS Lambda Handler
──────────────────
Wraps the FastAPI app with Mangum so it runs on AWS Lambda.
This file is the entry point Lambda will call.
"""

from api.main import app
from mangum import Mangum

# Mangum adapts FastAPI (ASGI) to work as a Lambda function
handler = Mangum(app, lifespan="off")
