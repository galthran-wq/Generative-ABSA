import os
from pathlib import Path
import argparse
from copy import deepcopy

from razdel import sentenize


def main(src, dst, keep_empty=False):
    os.makedirs(dst, exist_ok=True)

    for file in os.listdir(src):
        file_path = Path(src) / file
        lines = open(file_path).readlines()
        entries = []
        n_triplets = 0

        for i in range(len(lines)):
            line = lines[i].strip()
            text, triplets = line.split("####")
            triplets = eval(triplets)
            n_triplets += len(triplets)
            triplets_aspects = [min(triplet[0]) for triplet in triplets]
            triplets_opinions = [min(triplet[1]) for triplet in triplets]
            line_entries = []
            offset = 0
            sents = [ el.text for el in list(sentenize(text)) ]

            assert sum(len(sent.split(" ")) for sent in sents) == len((text.split()))

            for sent in sents:
                sent_tokens = sent.split(" ")
                sent_aspects = [
                    i 
                    for i, (aspect_start_token, opinion_start_token) in enumerate(zip(triplets_aspects, triplets_opinions)) 
                    if (
                        offset <= aspect_start_token < len(sent_tokens) + offset and
                        offset <= opinion_start_token < len(sent_tokens) + offset 
                    )
                ]
                if len(sent_aspects) != 0:
                    sent_triplets = [
                        deepcopy(triplet) 
                        for i, triplet in enumerate(triplets) if i in sent_aspects
                    ]
                    for triplet in sent_triplets:
                        for j in range(2):
                            for i in range(len(triplet[j])):
                                triplet[j][i] -= offset
                                assert triplet[j][i] < len(sent_tokens), (triplet[j][i], len(sent_tokens))
                    line_entries.append((sent, sent_triplets))
                elif keep_empty:
                    line_entries.append((sent, []))
                offset += len(sent_tokens)
            entries.append(line_entries)

        n_new_triplets = sum(len(entry[1]) for entry_set in entries for entry in entry_set)
        print(
            f"{n_triplets - n_new_triplets} ({round(1 - n_new_triplets/n_triplets, 2) * 100}%) " +
            f"entries in {file} contained outplace opinions and were therefore removed"
        )

        entries_pooled = [
            entry
            for entry_set in entries
            for entry in entry_set
        ]

        with open(dst/ file, "w") as f:
            f.writelines([
                f"{text}####{str(triplet)}\n"
                for (text, triplet) in entries_pooled
            ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # basic settings
    parser.add_argument("--src", default='bank_3200', type=str, required=False)
    parser.add_argument("--dst", default='bank_3200_sentenized', type=str, required=False)
    parser.add_argument("--keep-empty", action="store_true")
    args = parser.parse_args()
    data_dir = Path("./data/aste/")
    src = data_dir / args.src
    dst = data_dir / args.dst
    main(src, dst, keep_empty=args.keep_empty)