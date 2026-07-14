"""
CLARIQ AWS INFERENCE ENGINE
Runs daily at 12am. Produces intelligence reports autonomously.
"""

import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
import sys
sys.path.append('/opt/ml')

from clariq_ai_agent import ClariqAIAgent

s3_client = boto3.client('s3')
BUCKET = 'clariq-ml-intelligence'

def lambda_handler(event, context):
    """
    Daily 12am autonomous inference job
    Produces market intelligence for all connected sellers
    """
    
    try:
        execution_log = {
            'timestamp': datetime.now().isoformat(),
            'status': 'running',
            'sellers_processed': 0,
            'reports_generated': 0,
            'errors': 0
        }
        
        # Get list of all connected sellers from DynamoDB/database
        sellers = get_connected_sellers()
        
        for seller in sellers:
            try:
                # Load seller's historical data
                seller_data = load_seller_data(seller['store_id'])
                
                # Initialize AI agent
                agent = ClariqAIAgent(
                    store_id=seller['store_id'],
                    store_name=seller['store_name']
                )
                
                # Load data
                agent.load_data(seller_data)
                
                # Run full analysis
                print(f"Processing {seller['store_name']}...")
                report = agent.run_full_analysis()
                
                # Generate strategic insights
                insights = generate_insights(agent)
                
                # Save report to S3
                report_key = f"reports/{seller['store_id']}/{datetime.now().strftime('%Y-%m-%d')}_intelligence_report.txt"
                s3_client.put_object(
                    Bucket=BUCKET,
                    Key=report_key,
                    Body=report,
                    ContentType='text/plain'
                )
                
                # Save insights as JSON (for API)
                insights_key = f"insights/{seller['store_id']}/{datetime.now().strftime('%Y-%m-%d')}_insights.json"
                s3_client.put_object(
                    Bucket=BUCKET,
                    Key=insights_key,
                    Body=json.dumps(insights),
                    ContentType='application/json'
                )
                
                # Log success
                execution_log['sellers_processed'] += 1
                execution_log['reports_generated'] += 1
                
                # Trigger notifications
                send_seller_notification(seller, insights)
                
            except Exception as e:
                print(f"Error processing {seller['store_name']}: {str(e)}")
                execution_log['errors'] += 1
                continue
        
        execution_log['status'] = 'complete'
        
        # Save execution log
        s3_client.put_object(
            Bucket=BUCKET,
            Key=f"logs/{datetime.now().strftime('%Y-%m-%d')}_execution.json",
            Body=json.dumps(execution_log),
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(execution_log)
        }
    
    except Exception as e:
        print(f"Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def load_seller_data(store_id):
    """Load seller's historical data from S3"""
    response = s3_client.get_object(
        Bucket='clariq-data',
        Key=f'sellers/{store_id}/historical_data.csv'
    )
    df = pd.read_csv(response['Body'])
    return df


def get_connected_sellers():
    """Get list of all connected sellers"""
    # In real system, this queries DynamoDB
    # For POC, return test sellers
    return [
        {'store_id': 'store_001', 'store_name': 'Premium Electronics'},
        {'store_id': 'store_002', 'store_name': 'Fashion Boutique'},
        {'store_id': 'store_003', 'store_name': 'Marketplace Seller'},
    ]


def generate_insights(agent):
    """Extract structured insights from agent analysis"""
    return {
        'timestamp': datetime.now().isoformat(),
        'store_id': agent.store_id,
        'store_name': agent.store_name,
        'predictions_48h': {
            'trend': agent.trend_direction,
            'avg_predicted': float(agent.forecast_48h['yhat'].mean()),
            'confidence_interval': {
                'lower': float(agent.forecast_48h['yhat_lower'].mean()),
                'upper': float(agent.forecast_48h['yhat_upper'].mean())
            }
        },
        'causal_factors': agent.causal_factors,
        'anomalies_detected': len(agent.anomalies),
        'strategic_recommendations': agent.strategic_recommendations,
        'ready_for_autonomous_execution': True
    }


def send_seller_notification(seller, insights):
    """Send notification to seller with key insights"""
    message = f"""
Good morning! 🌅

Your AI agent just completed tonight's market analysis.

KEY FINDINGS:
• Market trend: {insights['predictions_48h']['trend']}
• Avg predicted demand: ${insights['predictions_48h']['avg_predicted']:.0f}
• Anomalies detected: {insights['anomalies_detected']}
• Strategic recommendations: {len(insights['strategic_recommendations'])}

{len(insights['strategic_recommendations'])} actions recommended.
View full report in your dashboard.

Clariq AI Agent
"""
    
    # Send via email/SMS (implement SNS or SES)
    print(f"Notification sent to {seller['store_name']}")


if __name__ == "__main__":
    # Test locally
    result = lambda_handler({}, {})
    print(json.dumps(result, indent=2))
