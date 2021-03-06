#!/usr/bin/env python3

import os
import warnings
from typing import List, Tuple, Iterable

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_distances

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable: Iterable, **kwargs) -> Iterable:
        return iterable


def read_explanations(path: str) -> List[Tuple[str, str]]:
    header = []
    uid = None

    df = pd.read_csv(path, sep='\t', dtype=str)

    for name in df.columns:
        if name.startswith('[SKIP]'):
            if 'UID' in name and not uid:
                uid = name
        else:
            header.append(name)

    if not uid or len(df) == 0:
        warnings.warn('Possibly misformatted file: ' + path)
        return []

    return df.apply(lambda r: (r[uid], ' '.join(str(s) for s in list(r[header]) if not pd.isna(s))), 1).tolist()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nearest', type=int, default=100)
    parser.add_argument('tables')
    parser.add_argument('questions', type=argparse.FileType('r', encoding='UTF-8'))
    args = parser.parse_args()

    explanations = []

    for path, _, files in os.walk(args.tables):
        for file in files:
            explanations += read_explanations(os.path.join(path, file))

    if not explanations:
        warnings.warn('Empty explanations')

    df_q = pd.read_csv(args.questions, sep='\t', dtype=str)
    df_e = pd.DataFrame(explanations, columns=('uid', 'text'))

    vectorizer = TfidfVectorizer().fit(df_q['question']).fit(df_e['text'])
    X_q = vectorizer.transform(df_q['question'])
    X_e = vectorizer.transform(df_e['text'])
    X_dist = cosine_distances(X_q, X_e)

    for i_question, distances in tqdm(enumerate(X_dist), desc=args.questions.name, total=X_q.shape[0]):
        for i_explanation in np.argsort(distances)[:args.nearest]:
            print('{}\t{}'.format(df_q.loc[i_question]['QuestionID'], df_e.loc[i_explanation]['uid']))


if '__main__' == __name__:
    main()
