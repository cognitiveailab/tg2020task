#!/usr/bin/env python3

import math
import sys
import warnings
from collections import OrderedDict
from functools import partial
from typing import List, Dict, Callable, Optional

import pandas as pd


class ListShouldBeEmptyWarning(UserWarning):
    pass


def load_gold(filepath_or_buffer: str, sep: str = '\t') -> Dict[str, List[str]]:
    df = pd.read_csv(filepath_or_buffer, sep=sep, dtype=str)

    df = df[df['flags'].str.lower().isin(('success', 'ready'))]
    df = df[['QuestionID', 'explanation']]
    df.dropna(inplace=True)

    df['QuestionID'] = df['QuestionID'].str.lower()
    df['explanation'] = df['explanation'].str.lower()

    gold: Dict[str, List[str]] = OrderedDict()

    for _, row in df.iterrows():
        gold[row['QuestionID']] = [uid for e in row['explanation'].split()
                                       for uid, _ in (e.split('|', 1),)]

    return gold


def load_pred(filepath_or_buffer: str, sep: str = '\t') -> Dict[str, List[str]]:
    df = pd.read_csv(filepath_or_buffer, sep=sep, names=('question', 'explanation'), dtype=str)

    if any(df[field].isnull().all() for field in df.columns):
        raise ValueError('invalid format of the prediction dataset, possibly the wrong separator')

    pred: Dict[str, List[str]] = OrderedDict()

    for id, df_explanations in df.groupby('question'):
        pred[id.lower()] = list(OrderedDict.fromkeys(df_explanations['explanation'].str.lower()))

    return pred


def compute_ranks(true: List[str], pred: List[str]) -> List[int]:
    ranks: List[int] = []

    if not true or not pred:
        return ranks

    targets = list(true)

    # I do not understand the corresponding block of the original Scala code.
    for i, pred_id in enumerate(pred):
        for true_id in targets:
            if pred_id == true_id:
                ranks.append(i + 1)
                targets.remove(pred_id)
                break

    # Example: Mercury_SC_416133
    if targets:
        warnings.warn('targets list should be empty, but it contains: ' + ', '.join(targets), ListShouldBeEmptyWarning)

        for _ in targets:
            ranks.append(0)

    return ranks


def average_precision(ranks: List[int]) -> float:
    total = 0.

    if not ranks:
        return total

    for i, rank in enumerate(ranks):
        precision = float(i + 1) / float(rank) if rank > 0 else math.inf
        total += precision

    return total / len(ranks)


def mean_average_precision_score(gold: Dict[str, List[str]], pred: Dict[str, List[str]],
                                 callback: Optional[Callable[[str, float], None]] = None) -> float:
    total = 0.

    for id, explanations in gold.items():
        if id in pred:
            ranks = compute_ranks(explanations, pred[id])

            score = average_precision(ranks)

            if not math.isfinite(score):
                score = 0.

            total += score

            if callback:
                callback(id, score)

    mean_ap = total / len(gold) if gold else 0.

    return mean_ap


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--gold', type=argparse.FileType('r', encoding='UTF-8'), required=True)
    parser.add_argument('pred', type=argparse.FileType('r', encoding='UTF-8'))
    args = parser.parse_args()

    gold, pred = load_gold(args.gold), load_pred(args.pred)

    print('{:d} gold questions, {:d} predicted questions'.format(len(gold), len(pred)),
          file=sys.stderr)

    # callback is optional, here it is used to print intermediate results to STDERR
    mean_ap = mean_average_precision_score(
        gold, pred,
        callback=partial(print, file=sys.stderr)
    )

    print('MAP: ', mean_ap)


if '__main__' == __name__:
    main()
