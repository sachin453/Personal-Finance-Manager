import json
from langchain_core.tools import tool
import psycopg2, os
from psycopg2 import OperationalError, InterfaceError, DatabaseError



@tool
def run_sql_query_tool(query: str, params=None):
    """Execute a SQL query on the PostgreSQL database and return results."""
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute(query, params)

        # Only fetch results if it's a SELECT
        if query.strip().lower().startswith("select"):
            
            results = cur.fetchall()
        else:
            results = None
            conn.commit()

        return results

    except (OperationalError, InterfaceError, DatabaseError) as e:
        print(f"Database error: {e}")
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@tool
def insert_large_number_of_transactions(json_data, batch_size=100):
    """Insert a large number of transactions into the database in batches.
    json_data: List of transaction dicts with keys 'amount', 'category', 'date', 'description'.
    """
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        
        for i in range(0, len(json_data), batch_size):
            batch = json_data[i:i+batch_size]
            args_str = ','.join(cur.mogrify("(%s, %s, %s, %s)", 
                        (t['amount'], t['category'], t['date'], t['description'])).decode('utf-8') for t in batch)
            cur.execute("INSERT INTO transactions (amount, category, date, description) VALUES " + args_str)
        
        conn.commit()
        print("Large data inserted successfully!")
    
    except (OperationalError, InterfaceError, DatabaseError) as e:
        print(f"Database error: {e}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



sql_tools = [
    run_sql_query_tool,
    insert_large_number_of_transactions
]




