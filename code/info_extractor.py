import re
import spacy
import phonenumbers

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")


def extract_emails(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return emails


def extract_phone_numbers(text, region="US"):
    phone_numbers = []
    for match in phonenumbers.PhoneNumberMatcher(text, region):
        phone_numbers.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
    return phone_numbers


def extract_locations(text):
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return locations


def extractor(text):
    emails = extract_emails(text)
    phone_numbers = extract_phone_numbers(text)
    locations = extract_locations(text)

    print("Emails:", emails)
    print("Phone Numbers:", phone_numbers)
    print("Locations:", locations)
    return {"emails": emails, "phone_numbers": phone_numbers, "locations": locations}
