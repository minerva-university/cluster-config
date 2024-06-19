import os
import csv
import logging
import requests
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE
from time import sleep

# Configure logging
logging.basicConfig(
    filename="/var/log/ldap_sync/logfile.log",
    # Uncomment this line when running locally
    # filename="ldap_sync.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


# Function to download and parse the Google spreadsheet
def download_spreadsheet(spreadsheet_url):
    try:
        response = requests.get(spreadsheet_url)
        response.raise_for_status()
        rows = list(csv.reader(response.text.splitlines()))
        return rows[1:]  # Exclude the header row
    except Exception as e:
        logging.error(f"Error downloading spreadsheet: {e}")
        return []


# Function to connect to the LDAP server
def connect_ldap(server_address, bind_dn, bind_password):
    try:
        server = Server(server_address, get_info=ALL)
        conn = Connection(server, bind_dn, bind_password, auto_bind=True)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to LDAP server: {e}")
        return None


# Function to check if user exists in LDAP and create or update user
def process_users(rows, ldap_conn, base_dn):
    for count, row in enumerate(rows):
        email = row[1]
        first_name = row[2]
        last_name = row[3]
        password_hash = row[4]
        username = email.split("@")[0]

        search_filter = f"(uid={username})"
        ldap_conn.search(base_dn, search_filter, attributes=["userPassword"])

        if not ldap_conn.entries:
            # User does not exist, create new user
            user_dn = f"cn={username},ou=People,{base_dn}"
            success = ldap_conn.add(
                user_dn,
                ["inetOrgPerson", "posixAccount", "organizationalPerson", "person"],
                {
                    "sn": last_name,
                    "givenName": first_name,
                    "uid": username,
                    "uidNumber": str(10000 + count),
                    "gidNumber": "10001",
                    "mail": email,
                    "userPassword": password_hash,
                    "loginShell": "/bin/bash",
                    "homeDirectory": f"/home/{username}",
                },
            )
            if success:
                logging.info(f"Created new user: {username}")
            else:
                logging.error(f"Failed to create user {username}: {ldap_conn.result}")

        else:
            # User exists, check if password hash needs to be updated
            existing_password_hash = ldap_conn.entries[0]["userPassword"].value

            if isinstance(existing_password_hash, bytes):
                existing_password_hash = existing_password_hash.decode("utf-8")

            if existing_password_hash != password_hash:
                ldap_conn.modify(
                    ldap_conn.entries[0].entry_dn,
                    {"userPassword": [(MODIFY_REPLACE, [password_hash])]},
                )
                logging.info(f"Updated password hash for user: {username}")
            else:
                logging.info(f"No action needed for user: {username}")


# Main function
def main():
    import pdb

    pdb.set_trace()

    spreadsheet_url = os.getenv("LDAP_SPREADSHEET_URL")

    ldap_server = os.getenv("LDAP_SERVER")
    bind_dn = os.getenv("LDAP_BIND_DN")
    bind_password = os.getenv("LDAP_BIND_PASSWORD")
    base_dn = os.getenv("LDAP_BASE_DN")

    while True:
        rows = download_spreadsheet(spreadsheet_url)
        if rows:
            ldap_conn = connect_ldap(ldap_server, bind_dn, bind_password)
            if ldap_conn:
                process_users(rows, ldap_conn, base_dn)
                ldap_conn.unbind()
        else:
            logging.error("No rows to process or error downloading spreadsheet.")
        sleep(300)  # Wait for 5 min before checking again


if __name__ == "__main__":
    main()
