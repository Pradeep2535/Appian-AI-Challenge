from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains.llm import LLMChain

from constants import GOOGLE_API_KEY

def analyze_keywords(text):
    response_schemas = [
        ResponseSchema(name="name", description="The name of the person."),
        ResponseSchema(name="dob", description="The date of birth (DOB) of the person in YYYY-MM-DD format."),
        ResponseSchema(name="address", description="The address of the person."),
    ]


    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

    prompt_template = PromptTemplate(
        input_variables=["text"],
        template=(
            "You are an AI model that extracts specific fields from a document. "
            "Your task is to extract the following fields: name, date of birth (DOB), and address. "
            "If a field is not present, return null for that field.\n\n"
            "Here is the input text:\n{text}\n\n"
            "Respond with a JSON object that matches this schema:\n{format_instructions}"
        ),
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
    )

    genai.configure(api_key=GOOGLE_API_KEY)

    llm = GoogleGenerativeAI(model='gemini-1.5-flash',api_key=GOOGLE_API_KEY)

    chain = LLMChain(llm=llm, prompt=prompt_template, output_parser=output_parser)

    response = chain.run({"text":text})

    name = response['name']
    dob = response['dob']
    address = response['address']

    return name, dob, address

def identify_document(text):
    genai.configure(api_key=GOOGLE_API_KEY)
    llm = GoogleGenerativeAI(model='gemini-1.5-flash',google_api_key=GOOGLE_API_KEY)

    prompt_template = PromptTemplate(
            input_variables=["document_text", "document_names"],
            template=(
                "You are a document classifier. Your task is to classify a document based "
                "on its text content into one of the following document types:\n\n"
                "{document_names}\n\n"
                "If the document doesn't match any of these types, classify it as 'Others'.\n\n"
                "Document Text:\n{document_text}\n\n"
                "Output only the document type (e.g., Aadhaar, PAN, Others)."
            )
        )
    output_parser = StrOutputParser()

    document_names = ["Aadhaar", "PAN", "Gas Bill", "Electricity Bill", "Passport"]

    prompt = prompt_template.format( 
        document_text = text[:1000], #limiting
        document_names = ", ".join(document_names)

    )

    response = llm.invoke(prompt)
    parsed_response = output_parser.parse(response)

    return parsed_response.strip()


