import requests
import bs4
import os
from dotenv import load_dotenv
import psycopg2

JECC_URL = "http://www.jecc-ema.org/jecc/jecccfs.php"

# Load environment variables from .env file
load_dotenv()
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")


def fetch_jecc_logs(selected_date, selected_agency="All"):
    """
    Fetch logs from JECC for a given date and agency.
    """
    data = {
        "SelectedDate": selected_date,
        "SelectedAgency": selected_agency,
        "Submit": "Select",
    }
    try:
        response = requests.post(JECC_URL, data=data)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching logs: {e}")
        return ""


def parse_jecc_logs(logs_html):
    """
    Parse logs from JECC HTML content.
    """
    soup = bs4.BeautifulSoup(logs_html, "html.parser")
    post_content = soup.find("div", class_="art-PostContent")

    if not post_content:
        print("Couldn't find div with class 'art-PostContent'")
        return []

    inner_table = post_content.find("table").find("table")
    if not inner_table:
        print("Couldn't find the inner table")
        return []

    return [parse_log_row(row) for row in inner_table.find_all("tr")]


def parse_log_row(row):
    """
    Parse a single row of the log table into a dictionary.
    """
    cells = row.find_all("td")
    log_entry = {}
    separated_cell_list = [
        cell.get_text(separator="<br/>", strip=True).split("<br/>")
        for cell in cells[1::2]
    ]

    if len(separated_cell_list) < 3:
        return log_entry  # Return empty if not enough data

    log_entry["CFS #"] = int(separated_cell_list[0][0])
    log_entry["Address"] = (
        separated_cell_list[0][1] if len(separated_cell_list[0]) > 1 else None
    )
    log_entry["Call Type"] = (
        separated_cell_list[0][2] if len(separated_cell_list[0]) > 2 else None
    )
    log_entry["Time"] = (
        separated_cell_list[1][0] if len(separated_cell_list[1]) > 0 else None
    )
    log_entry["Apt/Suite"] = (
        separated_cell_list[1][1] if len(separated_cell_list[1]) > 1 else None
    )
    log_entry["Agency"] = (
        separated_cell_list[2][0] if len(separated_cell_list[2]) > 0 else None
    )
    log_entry["Disposition"] = (
        separated_cell_list[2][1] if len(separated_cell_list[2]) > 1 else None
    )
    log_entry["Incident #"] = (
        separated_cell_list[2][2] if len(separated_cell_list[2]) > 2 else None
    )

    return log_entry


def upsert_logs_to_postgres(logs_as_json):
    """
    Upsert logs to PostgreSQL using batch processing.
    """
    try:
        conn = psycopg2.connect(
            database=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT,
        )
        cursor = conn.cursor()
        upsert_query = """
            INSERT INTO jecc_logs (cfs_number, address, call_type, time, apt_suite, agency, disposition, incident_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cfs_number) DO UPDATE SET
                address = EXCLUDED.address,
                call_type = EXCLUDED.call_type,
                time = EXCLUDED.time,
                apt_suite = EXCLUDED.apt_suite,
                agency = EXCLUDED.agency,
                disposition = EXCLUDED.disposition,
                incident_number = EXCLUDED.incident_number;
        """
        # Prepare data tuples
        data_tuples = [
            (
                log["CFS #"],
                log["Address"],
                log["Call Type"],
                log["Time"],
                log["Apt/Suite"],
                log["Agency"],
                log["Disposition"],
                log["Incident #"],
            )
            for log in logs_as_json
        ]

        # Execute batch upsert
        psycopg2.extras.execute_batch(cursor, upsert_query, data_tuples)
        conn.commit()
    except Exception as e:
        print(f"Error during database operation: {e}")
    finally:
        cursor.close()
        conn.close()


def create_table_if_not_exists():
    try:
        conn = psycopg2.connect(
            database=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT,
        )
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jecc_logs (
                id SERIAL PRIMARY KEY,
                cfs_number INT UNIQUE,
                address TEXT NULL,
                call_type TEXT NULL,
                time TEXT NULL,
                apt_suite TEXT NULL,
                agency TEXT NULL,
                disposition TEXT NULL,
                incident_number TEXT NULL
            );
        """
        )
        conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        cursor.close()
        conn.close()


def test_database_connection():
    try:
        conn = psycopg2.connect(
            database=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT,
        )
        print("Database connection successful")
        conn.close()
    except Exception as e:
        print(f"Database connection failed: {e}")


if __name__ == "__main__":
    test_database_connection()
    create_table_if_not_exists()

    logs_html = fetch_jecc_logs("09/10/2024")
    logs_as_json = parse_jecc_logs(logs_html)
    for i, log in enumerate(logs_as_json):
        print(log)
        if i > 5:
            break

    upsert_logs_to_postgres(logs_as_json[0:1])
