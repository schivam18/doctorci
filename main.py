# main.py

from src.openai_client import OpenAIClient
from src.pdf_processing import PDFProcessor


def main():
    # Initialize the PDF Processor
    pdf_processor = PDFProcessor()

    pdf_processor.process_new_pdfs_to_csv()

    # # Initialize the OpenAI client
    # client = OpenAIClient()
    #
    # # Prepare your messages
    # messages = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {
    #         "role": "user",
    #         "content": "Write a haiku about recursion in programming."
    #     }
    # ]
    #
    # # Get chat completion and estimated cost
    # response = client.get_chat_completion(messages, max_tokens=50)
    # print("API Response:")
    # print(response)


if __name__ == "__main__":
    main()
