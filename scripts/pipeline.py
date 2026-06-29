import pandas as pd
import os
import logging
 
logging.basicConfig(
    filename='pipeline.log',       # where the log gets saved
    level=logging.INFO,            # capture INFO and anything more serious (WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s'   # timestamp - level - the actual message
)
 
pd.set_option('display.max_columns', None)  # Show all columns when printing DataFrames
 
 
# INSPECT FUNCTION
def inspect(df, name="dataset"):
    print(f"\n==== {name} ====")
    print(f"Shape: {df.shape}")
    print(f"\nData types:\n{df.dtypes}")
    print(f"\nMissing values:\n{df.isnull().sum()}")
    print(f"\nFirst 5 Rows:\n{df.head()}")
    print(f"\nBasic Stats:\n{df.describe()}")
 
 
def check_duplicates(df, name, subset=None):
    duplicate_rows = df.duplicated(subset=subset).sum()
    print(f"\n==== Duplicate check: {name} ====")
    print(f"Duplicate rows: {duplicate_rows}")
    if duplicate_rows > 0:
        print(df[df.duplicated(subset=subset, keep=False)])
 
 
# ---------------------------------------------------------------------------
# EXTRACT — now wrapped in error handling
# ---------------------------------------------------------------------------
def extract_csv(filepath, name):
    """
    Loads a CSV file safely.
    Fails LOUD and CLEAR if something's wrong, instead of crashing later
    in a confusing spot (like the merge step).
    """
    try:
        df = pd.read_csv(filepath)
        logging.info(f"loaded {name} -> {len(df)} rows")
        return df
    except FileNotFoundError:
        logging.error(f"{name} not found at path: {filepath}")
        raise
    except pd.errors.EmptyDataError:
        logging.error(f"{name} exists but is empty: {filepath}")
        raise
    except pd.errors.ParserError:
        logging.error(f"{name} is malformed/corrupted: {filepath}")
        raise
 
 
def transform(orders, customers, products):
    """
    Merges orders + customers + products, then calculates revenue.
    Checks for silently lost/broken rows along the way instead of
    just trusting the merge blindly.
    """
    starting_row_count = len(orders)
 
    # MERGE — orders is the "main list" (left), customers/products attach details
    orders_customers = orders.merge(customers, on="customer_id", how="left")
    full_data = orders_customers.merge(products, on="product_id", how="left")
 
    # CHECK: did we somehow gain or lose rows during the merge?
    if len(full_data) != starting_row_count:
        logging.warning(f"row count changed during merge. "
              f"Started with {starting_row_count}, ended with {len(full_data)}.")
 
    # CHECK: how many orders couldn't find a matching customer or product?
    missing_customer = full_data['customer_name'].isnull().sum()
    missing_product = full_data['product_name'].isnull().sum()
    if missing_customer > 0:
        logging.warning(f"{missing_customer} orders have no matching customer.")
    if missing_product > 0:
        logging.warning(f"{missing_product} orders have no matching product.")
 
    # CALCULATE REVENUE — guard against NaN quantity/price silently corrupting totals
    missing_qty_or_price = full_data[['quantity', 'price']].isnull().any(axis=1).sum()
    if missing_qty_or_price > 0:
        logging.warning(f"{missing_qty_or_price} rows have missing quantity or price "
              f"and will produce NaN revenue.")
 
    full_data["revenue"] = full_data["quantity"] * full_data["price"]
 
    logging.info(f"transform complete -> {len(full_data)} rows, "
          f"${full_data['revenue'].sum():.2f} total revenue")
 
    return full_data
 
 
def load(df, filepath, name):
    """
    Saves a DataFrame to CSV safely.
    Creates the output folder if it's missing, and confirms success/failure clearly.
    """
    folder = os.path.dirname(filepath)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
        logging.info(f"Created missing folder: {folder}")
 
    try:
        df.to_csv(filepath, index=False)
        logging.info(f"saved {name} -> {filepath} ({len(df)} rows)")
    except Exception as e:
        logging.error(f"failed to save {name} to {filepath}: {e}")
        raise
 
 
if __name__ == "__main__":
    # EXTRACT
    customers = extract_csv('data/customers.csv', 'customers')
    orders = extract_csv('data/orders.csv', 'orders')
    products = extract_csv('data/products.csv', 'products')
 
    # INSPECT
    inspect(customers, "customers")
    inspect(orders, "orders")
    inspect(products, "products")
 
    # CHECK DUPLICATES
    check_duplicates(customers, "customers", subset=["customer_id"])
    check_duplicates(orders, "orders", subset=["order_id"])
    check_duplicates(products, "products", subset=["product_id"])
 
    # TRANSFORM
    full_data = transform(orders, customers, products)
 
    # LOAD
    load(full_data, 'output/full_data.csv', 'full_data')