# SI 201 HW4 (Library Checkout System)
# Your name: King
# Your student id: 23442611
# Your email: kingjj@umich.edu
# Who or what you worked with on this homework (including generative AI like ChatGPT):
# If you worked with generative AI also add a statement for how you used it.
# e.g.:
# Asked ChatGPT for hints on debugging and for suggestions on overall code structure
#
# Did your use of GenAI on this assignment align with your goals and guidelines in your Gen AI contract? If not, why?
#
# --- ARGUMENTS & EXPECTED RETURN VALUES PROVIDED --- #
# --- SEE INSTRUCTIONS FOR FULL DETAILS ON METHOD IMPLEMENTATION --- #

from bs4 import BeautifulSoup
import re
import os
import csv
import unittest
import requests  # kept for extra credit parity


# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"
"""


def load_listing_results(html_path) -> list[tuple]:
    """
    Load file data from html_path and parse through it to find listing titles and listing ids.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples containing (listing_title, listing_id)
    """
    with open(html_path, "r", encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, "html.parser")

        listing_title = []
        listing_id = []

        # Find all listing titles and IDs
        for item in soup.find_all("div", class_="listing-title"):
            listing_title.append(item.get_text().strip())
        for item in soup.find_all("div", class_="listing-id"):
            listing_id.append(item.get_text().strip())

    return list(zip(listing_title, listing_id))


def get_listing_details(listing_id) -> dict:
    """
    Parse through listing_<id>.html to extract listing details.

    Args:
        listing_id (str): The listing id of the Airbnb listing

    Returns:
        dict: Nested dictionary in the format:
        {
            "<listing_id>": {
                "policy_number": str,
                "host_type": str,
                "host_name": str,
                "room_type": str,
                "location_rating": float
            }
        }
    """
    file_path = f'html_files/listing_{listing_id}.html'
    with open(file_path, "r", encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, "html.parser")

        # Extract details using appropriate tags and classes
        policy_number = soup.find("div", class_="policy-number").get_text().strip()
        host_type = soup.find("div", class_="host-type").get_text().strip()
        host_name = soup.find("div", class_="host-name").get_text().strip()
        room_type = soup.find("div", class_="room-type").get_text().strip()
        location_rating = float(soup.find("div", class_="location-rating").get_text().strip())

    return {
        listing_id: {
            "policy_number": policy_number,
            "host_type": host_type,
            "host_name": host_name,
            "room_type": room_type,
            "location_rating": location_rating
        }
    }


def create_listing_database(html_path) -> list[tuple]:
    """
    Use prior functions to gather all necessary information and create a database of listings.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples. Each tuple contains:
        (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
    """
    listings = load_listing_results(html_path)
    database = []

    for title, listing_id in listings:
        details = get_listing_details(listing_id)
        listing_data = details[listing_id]
        database.append((title, listing_id, listing_data["policy_number"], listing_data["host_type"], listing_data["host_name"], listing_data["room_type"], listing_data["location_rating"]))

    return database


def output_csv(data, filename) -> None:
    """
    Write data to a CSV file with the provided filename.

    Sort by Location Rating (descending).

    Args:
        data (list[tuple]): A list of tuples containing listing information
        filename (str): The name of the CSV file to be created and saved to

    Returns:
        None
    """
    data_sorted = sorted(data, key=lambda x: x[6], reverse=True)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Listing Title", "Listing ID", "Policy Number", "Host Type", "Host Name", "Room Type", "Location Rating"])
        writer.writerows(data_sorted)



def avg_location_rating_by_room_type(data) -> dict:
    """
    Calculate the average location_rating for each room_type.

    Excludes rows where location_rating == 0.0 (meaning the rating
    could not be found in the HTML).

    Args:
        data (list[tuple]): The list returned by create_listing_database()

    Returns:
        dict: {room_type: average_location_rating}
    """
    room_type_ratings = {}
    room_type_counts = {}

    for listing in data:
        room_type = listing[5]
        location_rating = listing[6]

        if location_rating != 0.0:
            if room_type not in room_type_ratings:
                room_type_ratings[room_type] = 0.0
                room_type_counts[room_type] = 0

            room_type_ratings[room_type] += location_rating
            room_type_counts[room_type] += 1

    avg_ratings = {room: (room_type_ratings[room] / room_type_counts[room]) for room in room_type_ratings}
    return avg_ratings


def validate_policy_numbers(data) -> list[str]:
    """
    Validate policy_number format for each listing in data.
    Ignore "Pending" and "Exempt" listings.

    Args:
        data (list[tuple]): A list of tuples returned by create_listing_database()

    Returns:
        list[str]: A list of listing_id values whose policy numbers do NOT match the valid format
    """
    invalid_listings = []
    pattern = re.compile(r"^STR-\d{7}$")

    for listing in data:
        listing_id = listing[1]
        policy_number = listing[2]

        if policy_number not in ["Pending", "Exempt"] and not pattern.match(policy_number):
            invalid_listings.append(listing_id)

    return invalid_listings

# EXTRA CREDIT
def google_scholar_searcher(query):
    """
    EXTRA CREDIT

    Args:
        query (str): The search query to be used on Google Scholar
    Returns:
        List of titles on the first page (list)
    """
    url = f"https://scholar.google.com/scholar?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    titles = []
    for item in soup.find_all("h3", class_="gs_rt"):
        title = item.get_text().strip()
        titles.append(title)

    return titles

class TestCases(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.search_results_path = os.path.join(self.base_dir, "html_files", "search_results.html")

        self.listings = load_listing_results(self.search_results_path)
        self.detailed_data = create_listing_database(self.search_results_path)

    def test_load_listing_results(self):
        'Check that the number of listings extracted is 18.'
        'Check that the first tuple is  ("Loft in Mission District", "1944564")'
        self.assertEqual(len(self.listings), 18)
        self.assertEqual(self.listings[0], ("Loft in Mission District", "1944564"))

    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]
        'Call get_listing_details() on each provided listing id and save results in a list'
        'Spot-check values by opening the corresponding listing_<id>.html files'
        'Check that the listing 467507 has the correct policy number "STR-0005349'
        'Check that the listing 1944564 has the correct host type "Superhost" and room'
        'type "Entire Room".' 
        'Check that listing 1944564 has the correct location rating 4.9.'
       
        for listing_id in html_list:
            details = get_listing_details(listing_id)
            listing_data = details[listing_id]

            if listing_id == "467507":
                self.assertEqual(listing_data["policy_number"], "STR-0005349")
            elif listing_id == "1944564":
                self.assertEqual(listing_data["host_type"], "Superhost")
                self.assertEqual(listing_data["room_type"], "Entire Room")
                self.assertEqual(listing_data["location_rating"], 4.9)

    def test_create_listing_database(self):
        'Check that each tuple in detailed_data has exactly 7 elements.' 
        'Spot-check  the  last  tuple  is  ("Guest  suite  in  Mission  District'
        '"467507",  "STR-0005349",  "Superhost",  "Jennifer",  "EntireRoom", 4.8).'

        for listing in self.detailed_data:
            self.assertEqual(len(listing), 7)

    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")

        'Call output_csv() to write the detailed_data to a CSV file.'
        'Read the CSV back in and store rows in a list.'
        'Check that the first data row matches ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"].'

        output_csv(self.detailed_data, out_path)
        with open(out_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        os.remove(out_path)

    def test_avg_location_rating_by_room_type(self):
        'Call avg_location_rating_by_room_type() and save the output.'
        'Check that the average for "Private Room" is 4.9.'
        
        avg_ratings = avg_location_rating_by_room_type(self.detailed_data)
        self.assertAlmostEqual(avg_ratings.get("Private Room", 0), 4.

    def test_validate_policy_numbers(self):
        'all validate_policy_numbers() on detailed_data and save the result into a variable invalid_listings.'
        'Check that the list contains exactly "16204265" for this dataset.'
        
        invalid_listings = validate_policy_numbers(self.detailed_data)
        self.assertEqual(invalid_listings, ["16204265"])


def main():
    detailed_data = create_listing_database(os.path.join("html_files", "search_results.html"))
    output_csv(detailed_data, "airbnb_dataset.csv")


if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)