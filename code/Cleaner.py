import spacy
import Distill
# from sagemaker_inference import invoke_sagemaker_endpoint

nlp = spacy.load('en_core_web_sm')


def _base_clean(text):
    """
    Takes in text read by the parser file and then does the text cleaning.
    """
    text = Distill.tokenize(text)
    text = Distill.remove_stopwords(text)
    text = Distill.remove_tags(text)
    text = Distill.lemmatize(text)
    return text


def _reduce_redundancy(text):
    """
    Takes in text that has been cleaned by the _base_clean and uses set to reduce the repeating words
    giving only a single word that is needed.
    """
    return list(set(text))


def _get_target_words(text):
    """
    Takes in text and uses Spacy Tags on it, to extract the relevant Noun, Proper Noun words that contain words related to tech and JD. 

    """

    sent = " ".join(text)
    # result = invoke_sagemaker_endpoint(sent)  # NEW
    # target = result['tokens']
    # return target
    doc = nlp(sent)
    target = [token.text for token in doc if token.tag_ in ['NN', 'NNP']]
    return target


def Cleaner(text):
    sentence = []
    sentence_cleaned = _base_clean(text)
    sentence.append(sentence_cleaned)
    sentence_reduced = _reduce_redundancy(sentence_cleaned)
    sentence.append(sentence_reduced)
    sentence_targetted = _get_target_words(sentence_reduced)
    sentence.append(sentence_targetted)
    return sentence
