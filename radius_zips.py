# type: ignore
import argparse
import json
import pickle
from pathlib import Path

import pandas as pd
import requests

# Define the API details
URL = "https://zip-code-distance-radius.p.rapidapi.com/api/zipCodesWithinRadius"


# Function to get zip codes within a radius for a given zip code
def get_radius_zips(headers, zip_code, radius=10):
    try:
        response = requests.get(
            URL,
            headers=headers,
            params={"zipCode": zip_code, "radius": radius},
        )
        response.raise_for_status()
        data = response.json()
        return ", ".join(item["zipCode"] for item in data if "zipCode" in item)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for zip code {zip_code}: {e}")
    except ValueError as e:
        print(f"Error parsing JSON response for zip code {zip_code}: {e}")
    return ""


<<<<<<< HEAD
def in_order_merge(lst_of_lsts):
    zip_codes = []
    for zip_code_list in lst_of_lsts:
        for zip_code in zip_code_list:
            if zip_code not in zip_codes:
                zip_codes.append(zip_code)
    return zip_codes


# Apply the function to the zip column and create the radius_zips column
# Write the modified DataFrame to a new CSV file
=======
def correct_zip_code(zip_code):
    zip_str = str(zip_code)
    if zip_str.endswith(".0"):
        zip_str = zip_str[:-2]
    return zip_str.rjust(5, "0")


def create_provider_dict(df, col_name):
    provider_dict = {}
    for _, row in df.iterrows():
        zip_code = row["zip_code"]
        if zip_code not in provider_dict:
            provider_dict[zip_code] = []
        provider_dict[zip_code].append(row[col_name].upper())
    return provider_dict


def create_provider_row(zips_str, provider_dict):
    providers = []
    zips = [zip_code.strip() for zip_code in zips_str.split(",")]
    for zip_code in zips:
        if zip_code in provider_dict:
            providers.extend(provider_dict[zip_code])
    return ", ".join(providers)


>>>>>>> 12c413e (Add standard provider row code functions)
def find_radius_zips(df, headers, radius):
    if not Path(f"cache{radius}.pickle").exists():
        with open(f"cache{radius}.pickle", "wb") as cache_maker:
            pickle.dump(dict(), cache_maker)
    with open(f"cache{radius}.pickle", "r+b") as cache_file:
        cache = pickle.load(cache_file)
        for idx, row in df.iterrows():
            changed_cache = False
            zip_codes = [a.strip() for a in row["total_zips"].split(",")]
            for zip_code in zip_codes:
                if zip_code not in cache:
                    cache[zip_code] = get_radius_zips(headers, zip_code, radius)
                    changed_cache = True
            df.loc[idx, "radius_zips"] = ",".join(
                in_order_merge(cache[zip_code] for zip_code in zip_codes)
            )
            if changed_cache:
                cache_file.seek(0)
                pickle.dump(cache, cache_file)
                cache_file.truncate()
                cache_file.flush()
            print(f"Completed: {((idx + 1) * 100)/ len(df.index):.2f}%", end="\r")
    return df


def main():
    parser = argparse.ArgumentParser(
        prog="radius_zips",
        description="Read A CSV describing different cities, and return all zip codes within a radius",
    )
    parser.add_argument("input_file", help="Input CSV File", nargs=1)
    parser.add_argument(
        "output_file",
        help='Output CSV. Defaults to input_name with the extension ".out.csv"',
        nargs="?",
    )
    parser.add_argument(
        "-r",
        "--radius",
        type=int,
        default=10,
        help="Radius in miles within which to search for Zip Codes",
    )
    args = parser.parse_args()
    df = pd.read_csv(args.input_file[0])
    if "total_zips" not in df.columns:
        raise KeyError(
            "'total_zips' column not found in the CSV file. Please check the column name."
        )
    output_file_path = (
        f"{Path(args.input_file[0]).stem}.out.csv"
        if not args.output_file
        else args.output_file
    )
    with open("secrets.json", "r") as secrets:
        headers: dict[str, str] = json.load(secrets)

    df = find_radius_zips(df, headers, args.radius)
    df.to_csv(output_file_path, index=False)


if __name__ == "__main__":
    main()
