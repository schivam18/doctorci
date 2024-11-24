import json

attributes_json_path = 'data/base_attributes.json'
# Load the attributes from the JSON file
with open(attributes_json_path, 'r') as file:
    attributes_data = json.load(file)

sample_output_json = '''
{
  "drugs": [
    { "drug_name": "example_drug_name"
      "attributes": [
        {
          "attribute_name": "example_attribute_name",
          "attribute_value": "example_attribute_value"
        }
        /* Additional attribute objects */
      ]
    }
    /* Additional drug objects */
  ]
}
'''


def generate_extraction_prompt(abstract_text, sample_attributes_dict=attributes_data, output_format=sample_output_json):

    # Start constructing the prompt
    prompt = (
        "Please analyze the following abstract and perform the following tasks:\n\n"
        "1. **Identify the main drugs** being assessed in the abstract.\n\n"
        "2. **For each identified drug**, extract relevant attributes you find in the abstract.\n\n"
        "   - **Note:** The following list of sample attributes is provided for inspiration. "
        "You are not limited to these attributes and may include other relevant and important attributes found in the "
        "abstract.\n\n"
    )

    # Add Categories and Sample Attributes
    for category, attributes in sample_attributes_dict.items():
        prompt += f"**{category}:**\n"
        for attr in attributes:
            prompt += f"- {attr}\n"
        prompt += "\n"

    # Add instructions for the JSON output
    prompt += (
        "3. **Provide your response in the following JSON format:**\n\n"
        "```json\n"
        f"{output_format}\n"
        "```\n\n"
        "Please ensure that your response is accurate and formatted correctly.\n\n"
        "**Abstract:**\n\n"
        f"{abstract_text}\n"
    )

    return prompt
