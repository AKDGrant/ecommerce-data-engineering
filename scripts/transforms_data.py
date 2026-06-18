import pandas as pd 

pd.set_option('display.max_columns', None)  # Show all columns when printing DataFrames

#INSPECT FUNCTION
def inspect(df, name="dataset"):
    print(f"\n==== {name} ====")
    print(f"Shape: {df.shape}")  # rows and columns
    print(f"\nData types:\n{df.dtypes}") # Are types correct?
    print(f"\nMissing values:\n{df.isnull().sum()}") # any missing values?
    print(f"\nFirst 5 Rows:\n{df.head()}") # what does the data look like?
    print(f"\nBasic Stats:\n{df.describe()}")  # min, max, mean, std for numeric columns

def check_duplicates(df, name, subset=None):
    duplicate_rows = df.duplicated(subset=subset).sum()
    print(f"\n==== Duplicate check: {name} ====")
    print(f"Duplicate rows: {duplicate_rows}")
    if duplicate_rows > 0:
        print(df[df.duplicated(subset=subset, keep=False)])
        
# EXTRACT - load the data
customers = pd.read_csv('data/customers.csv')
orders = pd.read_csv('data/orders.csv')
products = pd.read_csv('data/products.csv')

# INSPECT - understand the data
inspect(customers, "customers")
inspect(orders, "orders")
inspect(products, "products")

# CHECK DUPLICATES
check_duplicates(customers, "customers", subset=["customer_id"])
check_duplicates(orders, "orders", subset=["order_id"])
check_duplicates(products, "products", subset=["product_id"])

# MERGE - combine the data
orders_customers = orders.merge(customers, on="customer_id", how="left")
full_data = orders_customers.merge(products, on="product_id", how="left")
print(full_data)

# TRANSFORM - add a new column for revenue
full_data["revenue"] = full_data["quantity"] * full_data["price"]

# Now we can see the revenue for each order, along with the customer and product details
print(full_data[['customer_name', 'product_name', 'price', 'quantity', 'revenue']])

# Calculate total revenue
total_revenue = full_data['revenue'].sum()
print(f"Total Revenue: ${total_revenue:.2f}")

# step 1 — group and add up
customer_revenue = full_data.groupby('customer_name')['revenue'].sum().reset_index()

# step 2 — sort highest to lowest
customer_revenue = customer_revenue.sort_values(by='revenue', ascending=False)

# step 3 — clean up the index numbers
customer_revenue = customer_revenue.reset_index(drop=True)

# NOW print — after all 3 steps are done
print(customer_revenue)

# step 1 — group and add up
Product_revenue = full_data.groupby('product_name')['revenue'].sum().reset_index()

# step 2 — sort highest to lowest
Product_revenue = Product_revenue.sort_values(by='revenue', ascending=False)

# step 3 — clean up the index numbers
Product_revenue = Product_revenue.reset_index(drop=True)

# NOW print — after all 3 steps are done
print(Product_revenue)

# Find the top 3 products and customers by revenue
top_products = Product_revenue.sort_values(by='revenue', ascending=False, inplace=False).head(3)
print(top_products)

top_customers = customer_revenue.sort_values(by='revenue', ascending=False, inplace=False).head(3)
print(top_customers)

# Add a new column to identify the type of insight
top_customers["type"] = "customer"
top_products["type"] = "product"

top_customers = top_customers.rename(columns={'customer_name': 'name'})
top_products = top_products.rename(columns={'product_name': 'name'})

insights = pd.concat([top_customers, top_products], ignore_index=True)

print(insights)

final_report = full_data.copy()
print(final_report.head())

full_data.to_csv('output/full_data.csv', index=False)
customer_revenue.to_csv("output/customer_revenue.csv", index=False)
Product_revenue.to_csv("output/product_revenue.csv", index=False)