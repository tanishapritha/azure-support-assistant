import azure.functions as func
import json
import logging
from etl.pipeline import ETLPipeline
import pandas as pd
import io

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger = logging.getLogger(__name__)
    logger.info('Processing new ticket ingestion request.')

    try:
        req_body = req.get_json()
        if not isinstance(req_body, list):
            return func.HttpResponse(
                json.dumps({"error": "Payload must be a list of tickets"}),
                status_code=400,
                mimetype="application/json"
            )

        # Validate fields
        required_fields = ["ticket_id", "customer_name", "timestamp", "category", "question", "resolution"]
        for ticket in req_body:
            for field in required_fields:
                if field not in ticket:
                    return func.HttpResponse(
                        json.dumps({"error": f"Missing field: {field}"}),
                        status_code=400,
                        mimetype="application/json"
                    )

        # Process via ETL
        df = pd.DataFrame(req_body)
        pipeline = ETLPipeline()
        
        # We can modify the pipeline to accept a dataframe directly
        pipeline.store_in_postgres(df)
        pipeline.store_in_search(df)

        return func.HttpResponse(
            json.dumps({"status": "success", "message": f"Processed {len(req_body)} tickets"}),
            status_code=200,
            mimetype="application/json"
        )

    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON payload"}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )
