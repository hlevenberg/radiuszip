import argparse
import json
import pickle
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import NamedTuple, TypeVar

import pandas as pd
import requests


class Provider(NamedTuple):
    file_name: str
    name_column: str
    zip_column: str
    output_column: str


def create_provider(dct: Mapping[str, str]):
    zip_col = dct["zip_column"] if "zip_column" in dct else "zip_code"
    output_col = dct["output_column"] if "output_column" in dct else dct["name_column"]
    return Provider(dct["file_name"], dct["name_column"], zip_col, output_col)


# Define the API details
URL = "https://zip-code-distance-radius.p.rapidapi.com/api/zipCodesWithinRadius"


# Function to get zip codes within a radius for a given zip code
def get_radius_zips(headers: Mapping[str, str], zip_code: str, radius: int = 10):
    try:
        response = requests.get(
            URL,
            headers=headers,
            params={"zipCode": zip_code, "radius": radius},
        )
        response.raise_for_status()
        data: list[Mapping[str, str]] = response.json()
        return ", ".join(item["zipCode"] for item in data if "zipCode" in item)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for zip code {zip_code}: {e}")
    except ValueError as e:
        print(f"Error parsing JSON response for zip code {zip_code}: {e}")
    return ""


T = TypeVar("T")


def in_order_merge(lst_of_lsts: Iterable[Iterable[T]]):
    merged_iter: list[T] = []
    for intermediate_iter in lst_of_lsts:
        for item in intermediate_iter:
            if item not in merged_iter:
                merged_iter.append(item)
    return merged_iter


# Apply the function to the zip column and create the radius_zips column
# Write the modified DataFrame to a new CSV file
def correct_zip_code(zip_code):
    zip_str = str(zip_code)
    if zip_str.endswith(".0"):
        zip_str = zip_str[:-2]
    return zip_str.rjust(5, "0")


def create_provider_dict(df, provider_col_name, zip_col_name):
    provider_dict: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        zip_code: str = row[zip_col_name]
        if zip_code not in provider_dict:
            provider_dict[zip_code] = []
        provider_dict[zip_code].append(row[provider_col_name].upper())
    return provider_dict


def create_provider_row(zips_str: str, provider_dict: Mapping[str, list[str]]) -> str:
    zips = [zip_code.strip() for zip_code in zips_str.split(",")]
    return ", ".join(
        in_order_merge(
            provider_dict[zip_code] for zip_code in zips if zip_code in provider_dict
        )
    )


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
        "-s",
        "--search",
        action="store_true",
        help="Run radius search, accessing the distance API",
    )
    parser.add_argument(
        "-r",
        "--radius",
        type=int,
        default=10,
        help="Radius in miles within which to search for Zip Codes. Does nothing without -s",
    )
    args = parser.parse_args()
    df = pd.read_csv(args.input_file[0])
    if args.search:
        if "total_zips" not in df.columns:
            raise KeyError(
                "'total_zips' column not found in the CSV file. Please check the column name."
            )
        with open("secrets.json", "r") as secrets:
            headers: dict[str, str] = json.load(secrets)

        df = find_radius_zips(df, headers, args.radius)
    output_file_path = (
        f"{Path(args.input_file[0]).stem}.out.csv"
        if not args.output_file
        else args.output_file
    )
    if Path("providers.json").exists():
        if "radius_zips" not in df.columns:
            raise KeyError("'radius_zips' necessary for Provider column creation")
        with open("providers.json", "r") as provider_file:
            providers: list[Provider] = json.load(
                provider_file, object_hook=create_provider
            )
        for provider in providers:
            if not Path(provider.file_name).exists():
                print(f"File {provider.file_name} does not exist!")
                continue
            provider_df = pd.read_csv(provider.file_name)
            provider_df[provider.zip_column] = provider_df[provider.zip_column].apply(
                correct_zip_code
            )
            provider_dict = create_provider_dict(
                provider_df, provider.name_column, provider.zip_column
            )
            df[provider.output_column] = df.apply(
                lambda row: create_provider_row(row["radius_zips"], provider_dict),
                axis=1,
            )

    df.to_csv(output_file_path, index=False)


if __name__ == "__main__":
    main()
