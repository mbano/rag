import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

_stopwords = set(stopwords.words("english"))
_translator = str.maketrans("", "", string.punctuation)


def clean_tokens(text: str):
    """
    Tokenize and clean English text for keyword-based retrieval.
    """
    tokens = word_tokenize(text.lower().translate(_translator))
    return [t for t in tokens if t not in _stopwords and len(t) > 2]
