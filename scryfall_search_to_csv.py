#!/usr/bin/env python

import requests
import pandas as pd


def scryfall_json_to_csv(data, csv_filename, selectlist=[],
                         deselectlist=[], sep=";"):
    """
        Saves a Scryfall.com search result to a CSV file

            Parameters:
                data (DataFrame): the data returned by a Scryfall search json
                    according to Scryfall's syntax.
                csv_filename (string): the full path and filename of the CSV to
                    be saved.
                selectlist (list): list of column names to be included in the
                    CSV.
                deselectlist (list): list of column names to be excluded from
                    the CSV. If both selectlist and deselectlist are given
                    together, only selectlist is used.
                sep (string): the separator character of the CSV, default ";".
    """
    if (len(selectlist) == 0 and len(deselectlist) > 0):
        selectlist = [x for x in data.columns if x not in deselectlist]

    if (len(selectlist) > 0):
        data_to_write = data[selectlist]
    else:
        data_to_write = data

    data_to_write.to_csv(csv_filename, index=False, encoding='utf-8', sep=sep)


def scryfall_search_to_json(search_str):
    """
        Performs a search on Scryfall.com and returns the result data as a list

            Parameters:
                search_str (string): the string representing the search
                    according to Scryfall's syntax

            Returns:
                data (DataFrame): the search result data
    """
    request_str = (
        "https://api.scryfall.com/cards/search?q=%s&pretty=true" % search_str)

    print("Requesting '%s'..." % request_str)

    resp = requests.get(request_str)

    assert(resp.status_code == requests.codes.ok)

    resp_json = resp.json()
    total_cards = resp_json['total_cards']

    print("The search has produced %d results. Proceeding to download..." %
          total_cards)

    data = resp_json['data']

    print("Downloaded %d/%d results..." % (len(data), total_cards))

    # if the result is paginated, go through all pages
    while(resp_json['has_more']):
        resp = requests.get(resp_json['next_page'])

        assert(resp.status_code == requests.codes.ok)

        resp_json = resp.json()
        data = data + resp_json['data']

        print("Downloaded %d/%d results..." % (len(data), total_cards))

    return pd.DataFrame(data)


def fix_dfc_image_uris(data):
    '''Fix the missing image_uris for all DFC in the data'''
    return data.apply(copy_front_image, axis=1)


def copy_front_image(data):
    '''Copy the image_uris from the front face of DFC to the main card'''
    data_ = data
    if pd.isna(data_["image_uris"]):
        assert(isinstance(data_["card_faces"], list))
        data_["image_uris"] = data_["card_faces"][0]["image_uris"]
    return data_


if __name__ == "__main__":
    search_str = "game:Arena"
    selectlist = ["name", "rarity", "set", "set_name",
                  "booster", "arena_id", "foil", "image_uris"]
    csv_filename = "output.csv"

    data = scryfall_search_to_json(search_str)
    data = fix_dfc_image_uris(data)

    print("Finished download. Writing CSV file...")

    scryfall_json_to_csv(data, csv_filename, selectlist=selectlist)

    print("Done.")
