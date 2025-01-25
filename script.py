from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import time
import pyperclip


def start_tor():
    # Path to your tor.exe (from Tor Expert Bundle)
    tor_path = r"C:\Users\Tor Browser\Browser\TorBrowser\Tor\tor.exe"  # Update this path to the location of tor.exe

    # Start Tor process
    tor_process = subprocess.Popen(
        [tor_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # Ensures we get text output (not bytes)
        bufsize=1,  # Line-buffered output
    )
    print("Starting Tor process...")

    # Wait for "Bootstrapped 100%" in Tor output
    for line in iter(tor_process.stdout.readline, ""):
        print(line.strip())  # Optional: Print Tor's output in real-time
        if "Bootstrapped 100%" in line:
            print("Tor is ready!")
            break

    return tor_process


def setup_selenium_with_tor():
    # Set up Firefox options to use Tor
    options = Options()
    options.binary_location = (
        r"C:\Users\Tor Browser\Browser\firefox.exe"  # Update this path
    )
    options.add_argument("--headless")  # Optional: Run in headless mode
    options.add_argument("--private")  # Private browsing mode

    # Connect to Tor's SOCKS proxy
    proxy = "127.0.0.1:9050"  # Default Tor proxy
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "127.0.0.1")
    options.set_preference("network.proxy.socks_port", 9050)
    options.set_preference("network.proxy.socks_remote_dns", True)
    options.set_preference("permissions.default.image", 2)
    # profile.update_preferences()

    # Create the WebDriver instance
    driver = webdriver.Firefox(options=options)
    return driver


def read_google_sheet(sheet_url, sheet_name):
    # Authenticate with Google Sheets API
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope
    )
    client = gspread.authorize(credentials)

    # Open the Google Sheet
    sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
    return sheet.get_all_values()[1:]  # Read all data as a list of lists


def format_search_queries(sheet_data):
    search_queries = []
    for row in sheet_data:
        if (
            row[0] and row[1] and row[2] and row[3] == "Pending" and row[4] == "TV Show"
        ):  # Ensure all fields are not empty
            show_name = row[0]  # TV Show Name
            season = int(row[1])  # Convert Season Number to integer
            episode = int(row[2])  # Convert Episode Number to integer

            # Create the search query in the format 'ShowName S01E01'
            search_query = f"{show_name} S{season:02d}E{episode:02d}" 
            search_queries.append(search_query)

        elif row[0] and row[3] == "Pending" and row[4] == "Movie":
            movie_name = row[0]
            search_query = f"{movie_name}"
            search_queries.append(search_query)
        
        elif (
            row[0] and row[1] and row[2] =="" and row[3] == "Pending" and row[4] == "TV Show"
        ):  # Ensure all fields are not empty
            show_name = row[0]  # TV Show Name
            season = int(row[1])  # Convert Season Number to integer

            # Create the search query in the format 'ShowName S01E01'
            search_query = f"{show_name} Season {season}" 
            search_queries.append(search_query)

    return search_queries


def visit_and_search(driver, url, search_queries):
    driver.get(url)
    print(f"Visited: {url}")
    # print(f"Page Title: {driver.title}")

    try:
        # Locate the search input field using its attributes
        for query in search_queries: 
            search_input = driver.find_element(By.CSS_SELECTOR, "input[type='search']") # for each tv show to be downloaded
            search_input.clear()  # Clear the input field
            search_input.send_keys(query)
            driver.find_element(
                By.CSS_SELECTOR, "input[type='submit']"
            ).click()  # Input the search query
            print(f"Searched for: {query}")
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id='flist']"))
            )

            filter_list = driver.find_element(
                By.CSS_SELECTOR, "input[id='flist']"
            )
            filter_list.click()  # Click on the filter list
            filter_list.send_keys(query)
            print("Filtered list for: ", query)

            time.sleep(2)
            # Wait between queries (optional)
            driver.find_element(
                By.CSS_SELECTOR, "input[id='f_1080p']"
            ).click()  # filter for 1080p torrents
            time.sleep(2)
            span_elements = driver.find_elements(
                By.CSS_SELECTOR, 'span[class="item-icons"]'
            )

            # get the first visible element
            visible_span = None
            for span_element in span_elements:
                if span_element.is_displayed():  # Check if the element is visible
                    visible_span = span_element
                    break

            if visible_span:
                anchor_element = visible_span.find_element(By.TAG_NAME, "a")

                # Get the href attribute text
                magnet_link = anchor_element.get_attribute("href")
                print(f"The magnet link is: {magnet_link}")
                pyperclip.copy(magnet_link)
                print("Copied to clipboard!")
                # run torrent.py to open utorrent and download the file
                result = subprocess.run(
                    ["node", "index.js", magnet_link],
                    capture_output=True,
                    text=True  # Ensures output is in text format
                )

                # Print the output from index.js
                print("Output from index.js:")
                print(result.stdout)
                if result.stderr:
                    print("Error:")
                    print(result.stderr)
    
    
    except Exception as e:
                    print(f"Error interacting with the search input: {e}")


if __name__ == "__main__":

    google_sheet_url = "https://docs.google.com/spreadsheets/d/1BP8z2iqkm4d63aGFIi5YrmQ9GEyd2mnWNw-OuUmLY1o/edit"  # Update this URL
    sheet_name = "Sheet1"  # Update this sheet name

    # Start Tor (if necessary)
    tor_process = start_tor()

    try:
        # Read data from Google Sheet
        sheet_data = read_google_sheet(google_sheet_url, sheet_name)

        # Format data into search queries
        search_queries = format_search_queries(sheet_data)
        print("Search Queries:", search_queries)
        # Set up Selenium with Tor
        driver = setup_selenium_with_tor()

        # Visit the website and search
        visit_and_search(driver, "https://thepiratebay.org/", search_queries)
    finally:
        driver.quit()
        tor_process.terminate()
        print("Tor process terminated.")
