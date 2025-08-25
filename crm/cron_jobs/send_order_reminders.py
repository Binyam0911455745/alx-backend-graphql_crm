# File: crm/cron_jobs/send_order_reminders.py
import datetime
import os
import sys
from django.utils import timezone

# This block is crucial for a standalone script to access Django models and settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

# Define transport
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=False,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# Use variables for a more robust and secure GraphQL query
one_week_ago = timezone.now() - datetime.timedelta(days=7)
query = gql("""
    query getRecentOrders($order_date_cutoff: Date!) {
      allOrders(orderDate_Gte: $order_date_cutoff) {
        edges {
          node {
            id
            customer {
              email
            }
          }
        }
      }
    }
""")

# Execute and log results
try:
    result = client.execute(
        query,
        variable_values={"order_date_cutoff": one_week_ago.strftime("%Y-%m-%d")}
    )
    # The 'allOrders' key is what the corrected query uses
    orders = result.get("allOrders", {}).get("edges", [])

    now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("/tmp/order_reminders_log.txt", "a") as log:
        if not orders:
            log.write(f"{now} - No pending orders found.\n")
        else:
            for edge in orders:
                order = edge.get("node", {})
                if order:
                    log.write(f"{now} - Order ID: {order['id']}, Email: {order['customer']['email']}\n")
    print("Order reminders processed!")
except Exception as e:
    print(f"Error: {e}")
    with open("/tmp/order_reminders_log.txt", "a") as log:
        log.write(f"{now} - Error: {e}\n")