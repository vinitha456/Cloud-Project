import re

import spacy
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Define english stopwords
stop_words = stopwords.words('english')
nlp = spacy.load('en_core_web_sm')


def remove_stopwords(text, optional_params=False, optional_words=None):
    if optional_words is None:
        optional_words = []
    if optional_params:
        stop_words.append([a for a in optional_words])
    return [word for word in text if word not in stop_words]


def tokenize(text):
    """
        Removes any useless punctuations from the text
    """
    text = re.sub(r'[^\w\s]', '', text)
    return word_tokenize(text)


def lemmatize(text):
    """
        the input to this function is a list
    """
    str_text = nlp(" ".join(text))
    lemmatized_text = [word.lemma_ for word in str_text]
    return lemmatized_text


def _to_string(List):
    """
        the input parameter must be a list
    """
    string = " "
    return string.join(List)


def remove_tags(text):
    """
    Takes in Tags which are allowed by the user and then elimnates the rest of the words
    based on their Part of Speech (POS) Tags.
    """
    postags = ['PROPN', 'NOUN', 'ADJ', 'VERB', 'ADV']
    str_text = nlp(" ".join(text))
    filtered = [token.text for token in str_text if token.pos_ in postags]
    return filtered
