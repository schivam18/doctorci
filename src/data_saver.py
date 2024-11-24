# data_saver.py

import json
from src.repository import (
    insert_drug,
    insert_attribute,
    insert_drug_attribute,
    link_abstract_drug
)


def save_response_to_db(abstract_id, json_response):
    """
    Saves the data from the JSON response to the database.

    Parameters:
    - abstract_id: int, the ID of the abstract corresponding to this data.
    - json_response: dict, the parsed JSON response containing drugs and attributes.
    """
    # Ensure json_response is a dictionary
    if isinstance(json_response, str):
        json_response = json.loads(json_response)

    # Get the list of drugs
    drugs = json_response.get('drugs', [])
    if not drugs:
        print("No drugs found in the response.")
        return

    for drug_data in drugs:
        # Get the drug name
        drug_name = drug_data.get('drug_name')
        if not drug_name:
            print("Drug name missing in one of the entries. Skipping this drug.")
            continue

        # Insert the drug into the Drugs table and get the drug_id
        drug_id = insert_drug(drug_name)

        # Link the abstract to the drug
        link_abstract_drug(abstract_id, drug_id)

        # Get the attributes for the drug
        attributes = drug_data.get('attributes', [])
        if not attributes:
            print(f"No attributes found for drug '{drug_name}'.")
            continue

        for attr in attributes:
            attribute_name = attr.get('attribute_name')
            attribute_value = attr.get('attribute_value')
            attribute_units = attr.get('attribute_units')  # Optional

            if not attribute_name or attribute_value is None:
                print(f"Missing attribute name or value for drug '{drug_name}'. Skipping this attribute.")
                continue

            # Insert the attribute into the Attributes table and get the attribute_id
            attribute_id = insert_attribute(attribute_name)

            # Insert the drug attribute into the DrugAttributes table
            insert_drug_attribute(
                drug_id=drug_id,
                attribute_id=attribute_id,
                abstract_id=abstract_id,
                attribute_value=attribute_value,
                attribute_units=attribute_units
            )

            print(f"Saved attribute '{attribute_name}' for drug '{drug_name}'.")

    print("All data from the JSON response has been saved to the database.")
