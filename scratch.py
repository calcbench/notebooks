import pandas as pd
import spacy
import dask.dataframe as ddf

nlp = spacy.load(
    "en_core_web_sm", exclude=["tagger", "ner", "lemmatizer", "textcat", "parser"]
)
from dask.diagnostics import ProgressBar

ProgressBar().register()
import calcbench as cb

cb.enable_backoff()

contents_pkl_file = r"C:\Users\andre\Dropbox (Calcbench)\andrew\sp_500_contents.pkl"

disclosure_contents = pd.read_pickle(contents_pkl_file)

dask_dataframe = ddf.from_pandas(disclosure_contents, npartitions=10)

result = dask_dataframe.map_partitions(
    lambda d: d.apply(
        lambda disclosures: list(
            nlp.pipe(disclosure[:1000000] for disclosure in disclosures)
        )
    )
)

disclosure_embeddings = result.compute()

embeddings_file_name = (
    r"C:\Users\andre\Dropbox (Calcbench)\andrew\sp_500_spacy_embeddings.pkl"
)

disclosure_embeddings.to_pickle(embeddings_file_name)