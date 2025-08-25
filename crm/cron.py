"""
Django-crontab job definitions for CRM application
"""
import os
import django
import requests
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')
django.setup()


def log_crm_heartbeat():
    """
    Log a heartbeat message to confirm CRM application health.
    Logs in format: DD/MM/YYYY-HH:MM:SS CRM is alive
    """
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    heartbeat_message = f"{timestamp} CRM is alive"
    
    # Append heartbeat message to log file
    try:
        with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
            log_file.write(heartbeat_message + '\n')
    except Exception as e:
        print(f"Failed to write heartbeat log: {e}")
        print(heartbeat_message)


def update_low_stock():
    """
    Execute UpdateLowStockProducts mutation via GraphQL endpoint.
    Logs updated product names and new stock levels with timestamp.
    """
    graphql_endpoint = "http://localhost:8000/graphql"
    
    mutation = """
        mutation {
          updateLowStockProducts {
            updatedProducts {
              id
              name
              stock
            }
            message
          }
        }
    """

    headers = {"Content-Type": "application/json"}
    payload = {"query": mutation}

    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    try:
        response = requests.post(graphql_endpoint, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        
        updated_products_data = result.get("data", {}).get("updateLowStockProducts", {})
        updated_products = updated_products_data.get("updatedProducts", [])
        message = updated_products_data.get("message", "No message from mutation.")

        log_message = f"{timestamp} - {message}\n"
        
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            log_file.write(log_message)
            if updated_products:
                for product in updated_products:
                    product_log = f"[{timestamp}] Updated product: ID {product['id']}, Name: {product['name']}, New Stock: {product['stock']}\n"
                    log_file.write(product_log)

        print("Low stock update processed!")

    except requests.exceptions.RequestException as e:
        error_message = f"[{timestamp}] Error executing GraphQL mutation: {e}\n"
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            log_file.write(error_message)