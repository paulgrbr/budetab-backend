import os

TEMPLATE_FILE = "sql/init.sql.template"
OUTPUT_FILE = "sql/init.sql"

required_vars = ["POSTGRES_PUBLIC_USER", "POSTGRES_PUBLIC_PW", "POSTGRES_AUTH_USER", "POSTGRES_AUTH_PW"]

missing_vars = [var for var in required_vars if var not in os.environ]
if missing_vars:
    print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}")
    exit(1)

# Read environment variables
db_public_user = os.environ["POSTGRES_PUBLIC_USER"]
db_public_user_pw = os.environ["POSTGRES_PUBLIC_PW"]
db_auth_user = os.environ["POSTGRES_AUTH_USER"]
db_auth_user_pw = os.environ["POSTGRES_AUTH_PW"]

# Read the template file
try:
    with open(TEMPLATE_FILE, "r") as file:
        sql_content = file.read()
except FileNotFoundError:
    print(f"ERROR: Template file '{TEMPLATE_FILE}' not found!")
    exit(1)

# Replace placeholders with environment variable values
sql_content = sql_content.replace("{db_public_user}", db_public_user)
sql_content = sql_content.replace("{db_public_user_pw}", db_public_user_pw)
sql_content = sql_content.replace("{db_auth_user}", db_auth_user)
sql_content = sql_content.replace("{db_auth_user_pw}", db_auth_user_pw)

# Write the modified SQL to init.sql
with open(OUTPUT_FILE, "w") as file:
    file.write(sql_content)

print(f"Successfully generated '{OUTPUT_FILE}' with replaced values.")
