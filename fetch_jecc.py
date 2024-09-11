import requests
import bs4

JECC_URL = "http://www.jecc-ema.org/jecc/jecccfs.php"


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


if __name__ == "__main__":
    logs_html = fetch_jecc_logs("09/10/2024")
    logs_as_json = parse_jecc_logs(logs_html)
    for i, log in enumerate(logs_as_json):
        print(log)
        if i > 5:
            break
