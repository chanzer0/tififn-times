import requests
import bs4
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta

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
        # "SelectedDate": selected_date.strftime("%m/%d/%Y"),
        "SelectedAgency": selected_agency,
        "Submit": "Select",
    }
    try:
        response = requests.post(JECC_URL, data=data)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching logs for {selected_date.strftime('%m/%d/%Y')}: {e}")
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

    try:
        log_entry["CFS #"] = int(separated_cell_list[0][0])
    except ValueError:
        log_entry["CFS #"] = None

    log_entry["Address"] = (
        separated_cell_list[0][1] if len(separated_cell_list[0]) > 1 else None
    )
    log_entry["Call Type"] = (
        separated_cell_list[0][2] if len(separated_cell_list[0]) > 2 else None
    )

    time_str = separated_cell_list[1][0] if len(separated_cell_list[1]) > 0 else None
    if time_str:
        try:
            # Updated format string to handle 24-hour format
            log_entry["Time"] = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            log_entry["Time"] = None
    else:
        log_entry["Time"] = None

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


def upsert_logs_to_postgres(logs_as_json, log_date):
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
            INSERT INTO jecc_logs (cfs_number, address, call_type, log_date, log_time, apt_suite, agency, disposition, incident_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cfs_number, log_date) DO UPDATE SET
                address = EXCLUDED.address,
                call_type = EXCLUDED.call_type,
                log_time = EXCLUDED.log_time,
                apt_suite = EXCLUDED.apt_suite,
                agency = EXCLUDED.agency,
                disposition = EXCLUDED.disposition,
                incident_number = EXCLUDED.incident_number;
        """
        # Prepare data tuples
        data_tuples = [
            (
                log.get("CFS #"),
                log.get("Address"),
                log.get("Call Type"),
                log_date,
                log.get("Time"),
                log.get("Apt/Suite"),
                log.get("Agency"),
                log.get("Disposition"),
                log.get("Incident #"),
            )
            for log in logs_as_json
            if log.get("CFS #") is not None
        ]

        if data_tuples:
            # Execute batch upsert
            psycopg2.extras.execute_batch(cursor, upsert_query, data_tuples)
            conn.commit()
            print(f"Inserted/Updated {len(data_tuples)} records for {log_date}")
        else:
            print(f"No valid logs to upsert for {log_date}")
    except Exception as e:
        print(f"Error during database operation for {log_date}: {e}")
    finally:
        cursor.close()
        conn.close()


def create_table_if_not_exists():
    """
    Create the jecc_logs table in PostgreSQL if it does not exist.
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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jecc_logs (
                id SERIAL PRIMARY KEY,
                cfs_number INT,
                address TEXT NULL,
                call_type TEXT NULL,
                log_date DATE NOT NULL,
                log_time TIME NULL,
                apt_suite TEXT NULL,
                agency TEXT NULL,
                disposition TEXT NULL,
                incident_number TEXT NULL,
                UNIQUE (cfs_number, log_date)
            );
        """
        )
        conn.commit()
        print("Table 'jecc_logs' is ready.")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        cursor.close()
        conn.close()


def test_database_connection():
    # print(f"DATABASE_NAME: {DATABASE_NAME}")
    # print(f"DATABASE_USER: {DATABASE_USER}")
    # print(f"DATABASE_PASSWORD: {DATABASE_PASSWORD}")
    # print(f"DATABASE_HOST: {DATABASE_HOST}")
    # print(f"DATABASE_PORT: {DATABASE_PORT}")
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


def main():
    test_database_connection()
    create_table_if_not_exists()

    current_date = datetime.now().date()
    while True:
        print(f"Fetching data for {current_date.strftime('%m/%d/%Y')}...")
        logs_html = fetch_jecc_logs(current_date)
        if not logs_html.strip():
            print(f"No data found for {current_date.strftime('%m/%d/%Y')}. Stopping.")
            break

        logs_as_json = parse_jecc_logs(logs_html)
        if not logs_as_json:
            print(f"No logs parsed for {current_date.strftime('%m/%d/%Y')}. Stopping.")
            break

        upsert_logs_to_postgres(logs_as_json, current_date)

        # Move to the previous day
        current_date -= timedelta(days=1)


if __name__ == "__main__":
    main()
