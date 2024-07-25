# Nearby Zip Code Finder

Given a .csv file containing a

---

## Usage

```console
foo@bar:~$ python radius_zips.py test_file.csv # Finds zip codes within 10 miles of described cities
foo@bar:~$ python radius_zips.py -r 30 test_file.csv # Finds zip codes within 30 miles
foo@bar:~$ python radius_zips.py test_file.csv out.csv # Sets output to out.csv
foo@bar:~$ python radius_zips.py -h # Gets Help File
```

## Installation

1. Clone this repo
2. Create a virtual environment, and run `pip -r requirements.txt` to install the required dependencies.
3. Create a `secrets.json` file containing the headers described [here.](https://rapidapi.com/truvian-softworks-llc-truvian-softworks-llc-default/api/zip-code-distance-radius/playground/apiendpoint_bb623c08-aa10-471c-9796-7cea48d34c00)

```json
{
  "x-rapidapi-key": "Your Key Here",
  "x-rapidapi-host": "zip-code-distance-radius.p.rapidapi.com"
}
```

---

Created by @hlevenberg and @rgarber11.
