import calcbench as cb
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
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

class NumberNormalizingVectorizer(sklearn.feature_extraction.text.TfidfVectorizer):
    def build_tokenizer(self):
        tokenize = super(NumberNormalizingVectorizer, self).build_tokenizer()
        return lambda doc: list(number_normalizer(tokenize(doc)))

def number_normalizer(tokens):
    """ Map all numeric tokens to a placeholder.

    For many applications, tokens that begin with a number are not directly
    useful, but the fact that such a token exists can be relevant.  By applying
    this form of dimensionality reduction, some methods may perform better.
    """

    return ("#NUMBER" if token[0].isdigit() else token for token in tokens)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

get_period = lambda d: (d['calendar_year'])

def diffs(document_section, tickers):
    first_year = 2008
    end_year = 2018
    diffs = pd.DataFrame(index=tickers, columns=range(end_year, first_year, -1))
    for ticker in tqdm_notebook(tickers):
        docs = (d for d in cb.document_search(company_identifiers=[ticker], 
                                                document_name=document_section, 
                                                all_history=True) if d['calendar_period'] == 'Y')
        docs = sorted(docs, key=get_period)
        groups = []
        for k, g in itertools.groupby(docs, get_period):
            groups.append((k, list(g)))
        for (last_year, last_period_group), (this_year, this_period_group) in pairwise(groups):
            try:
                last_year_contents = ' '.join(BeautifulSoup(d.get_contents(), 'html.parser').text for d in last_period_group)
                this_year_contents = ' '.join(BeautifulSoup(d.get_contents(), 'html.parser').text for d in this_period_group)
            except:
                raise Exception("Exception Getting {0}".format(ticker))
            else:
                if not last_year_contents or not this_year_contents:
                    continue
                text_last_year = BeautifulSoup(last_year_contents, 'html.parser').text
                text_this_year = BeautifulSoup(this_year_contents, 'html.parser').text
                vectorizer = NumberNormalizingVectorizer(stop_words='english')
                X = vectorizer.fit_transform([text_this_year, text_last_year])
                distance = cosine(X[0].todense(), X[1].todense())
                diffs[this_year][ticker] = distance
    return diffs

def background_gradient(s, m, M, cmap='PuBu', low=0, high=0):
    # from https://stackoverflow.com/questions/38931566/pandas-style-background-gradient-both-rows-and-columns
    rng = M - m
    norm = colors.Normalize(m - (rng * low),
                            M + (rng * high))

    normed = norm(s.values)
    normed = [np.nan_to_num(n) for n in normed]
    c = [colors.rgb2hex(x) for x in plt.cm.get_cmap(cmap)(normed)]
    return ['background-color: %s' % color for color in c]

def highlight_largest_diffs(diffs):
    filled_df = diffs.loc[diffs.sum(axis=1).sort_values(ascending=False).index].round(3)
    return filled_df.style.apply(background_gradient, 
        cmap='Reds',
        m=filled_df.min().min(),
        M=filled_df.max().max(), 
        low=0,
        high=2.5)

if __name__ == "__main__":
    tickers = cb.tickers(index='DJIA') 
    document_section = "AccountingPolicies"
    d = diffs(document_section, tickers)
    highlight_largest_diffs(d)