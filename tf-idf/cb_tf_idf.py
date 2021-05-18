import calcbench as cb
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from bs4 import BeautifulSoup
from scipy.spatial.distance import cosine
from IPython.core.display import display, HTML
import sklearn
import itertools
from tqdm import tqdm_notebook
from matplotlib import colors
import matplotlib.pyplot as plt
import numpy as np
import pdb


class NumberNormalizingVectorizer(TfidfVectorizer):
    def build_tokenizer(self):
        tokenize = super(NumberNormalizingVectorizer, self).build_tokenizer()
        return lambda doc: list(number_normalizer(tokenize(doc)))


class NumberNormalizingCountVectorizer(CountVectorizer):
    def build_tokenizer(self):
        tokenize = super(NumberNormalizingCountVectorizer, self).build_tokenizer()
        return lambda doc: list(number_normalizer(tokenize(doc)))


def number_normalizer(tokens):
    """Map all numeric tokens to a placeholder.

    For many applications, tokens that begin with a number are not directly
    useful, but the fact that such a token exists can be relevant.  By applying
    this form of dimensionality reduction, some methods may perform better.
    """

    return ("#NUMBER" if token[0].isdigit() else token for token in tokens)


get_period = lambda d: (d["fiscal_year"])


def period_diffs(document_section, tickers):
    period_column_name = "fiscal_period"
    get_period = lambda search_result: "{fiscal_year}-{fiscal_period}".format(
        **search_result
    )
    return _diffs(document_section, tickers, period_column_name, get_period)


def _diffs(document_section, tickers, period_column_name, get_period):
    all_counts = pd.DataFrame()
    for ticker in tqdm_notebook(tickers):
        docs = cb.document_search(
            company_identifiers=[ticker],
            document_name=document_section,
            all_history=True,
        )
        docs = sorted(docs, key=lambda doc: doc.date_reported)
        docs = [
            {
                period_column_name: get_period(d),
                "contents": d.get_contents_text(),
                "ticker": ticker,
            }
            for d in docs
        ]
        docs = pd.DataFrame(data=docs).set_index(["ticker", period_column_name])
        docs = docs.drop_duplicates()
        docs = pd.concat([docs, docs.shift(1).add_prefix("previous_period_")], axis=1)
        docs = docs.assign(
            distance=docs[1:].apply(
                lambda row: document_distance(
                    row.contents, row.previous_period_contents
                ),
                axis=1,
            )
        )
        docs = docs.assign(
            word_count=count_vectorizer.fit_transform(docs.contents).sum(axis=1)
        )
        docs = docs.drop(["contents", "previous_period_contents"], axis=1)
        all_counts = pd.concat([all_counts, docs])
    return all_counts


vectorizer = NumberNormalizingVectorizer(stop_words="english")
count_vectorizer = NumberNormalizingCountVectorizer(stop_words="english")


def timestamp_diffs(document_section, tickers):
    return _diffs(
        document_section,
        tickers,
        "timestamp",
        lambda search_result: search_result.date_reported,
    )


def document_distance(docA, docB):
    X = vectorizer.fit_transform([docA, docB])
    return cosine(X[0].todense(), X[1].todense())


def background_gradient(s, m, M, cmap="PuBu", low=0, high=0):
    # from https://stackoverflow.com/questions/38931566/pandas-style-background-gradient-both-rows-and-columns
    rng = M - m
    norm = colors.Normalize(m - (rng * low), M + (rng * high))
    normed = norm(s.values)
    normed = [np.nan_to_num(n) for n in normed]
    c = [colors.rgb2hex(x) for x in plt.cm.get_cmap(cmap)(normed)]
    return ["background-color: %s" % color for color in c]


def highlight_largest_diffs(diffs):
    filled_df = diffs.loc[diffs.sum(axis=1).sort_values(ascending=False).index].round(3)
    return filled_df.style.apply(
        background_gradient,
        cmap="Reds",
        m=filled_df.min().min(),
        M=filled_df.max().max(),
        low=0,
        high=2.5,
    )


if __name__ == "__main__":
    tickers = cb.tickers(index="DJIA")
    document_section = "Business Description"
    d = diffs(document_section, tickers)
    highlight_largest_diffs(d)