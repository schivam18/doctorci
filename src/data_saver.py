# data_saver.py

import json
import logging

from src.logger_config import get_logger, log_performance
from src.repository import insert_attribute, insert_drug, insert_drug_attribute, link_abstract_drug


def save_response_to_db(abstract_id: int, json_response: str) -> None:
    """
    Saves the data from the JSON response to the database.

    Parameters:
    - abstract_id: int, the ID of the abstract corresponding to this data.
    - json_response: str, the JSON response containing treatment arms and attributes.
    """
    # Ensure json_response is a dictionary
    if isinstance(json_response, str):
        json_response = json.loads(json_response)

    # Get the treatment arms
    treatment_arms = json_response.get("treatment_arms", [])
    if not treatment_arms:
        print("No treatment arms found in the response.")
        return

    for arm in treatment_arms:
        # Get the drug name (Generic name)
        drug_name = arm.get("Generic name")
        if not drug_name:
            print("Drug name missing in one of the entries. Skipping this arm.")
            continue

        # Insert the drug into the Drugs table and get the drug_id
        drug_id = insert_drug(drug_name)

        # Link the abstract to the drug
        link_abstract_drug(abstract_id, drug_id)

        # Process all attributes from the treatment arm
        for attr_name, attr_value in arm.items():
            if attr_name == "Generic name":  # Skip the drug name as it's already processed
                continue

            if not attr_name or attr_value is None:
                print(f"Missing attribute name or value for drug '{drug_name}'. Skipping this attribute.")
                continue

            # Insert the attribute into the Attributes table and get the attribute_id
            attribute_id = insert_attribute(attr_name)

            # Insert the drug attribute into the DrugAttributes table
            insert_drug_attribute(
                drug_id=drug_id,
                attribute_id=attribute_id,
                abstract_id=abstract_id,
                attribute_value=str(attr_value),
                attribute_units=None,  # We don't have units in the current structure
            )

            print(f"Saved attribute '{attr_name}' for drug '{drug_name}'.")

    print("All data from the JSON response has been saved to the database.")


class DataSaver:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("DataSaver initialized")

    @log_performance
    def save_all_data(self, extracted_data_list):
        self.logger.info(f"Starting to save {len(extracted_data_list)} data records")
        saved_count = 0
        failed_count = 0
        for i, data in enumerate(extracted_data_list, 1):
            try:
                self.logger.debug(f"Saving record {i}/{len(extracted_data_list)}")
                self._save_single_record(data)
                saved_count += 1
                if i % 10 == 0:
                    self.logger.info(f"Progress: {i}/{len(extracted_data_list)} records processed")
            except Exception as e:
                failed_count += 1
                self.logger.error(f"Failed to save record {i}: {str(e)}")
        self.logger.info(f"Data saving complete - Success: {saved_count}, Failed: {failed_count}")

    def _save_single_record(self, data):
        try:
            self.logger.debug(f"Saving record with {len(data.get('treatments', []))} treatments")
            # ... existing save logic ...
            self.logger.debug("Record saved successfully")
        except Exception as e:
            self.logger.error(f"Database error while saving record: {str(e)}")
            raise
