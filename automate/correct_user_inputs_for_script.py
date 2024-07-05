#!/usr/bin/env python3
import json
import sys
from difflib import get_close_matches


def check_valid_word(word, values_list, cutoff=0.6):
    close_matches = get_close_matches(word.lower(), values_list, n=1,cutoff=cutoff)
    return close_matches[0] if close_matches else word

def main():
    input_word = sys.argv[1]
    values_list = json.loads(sys.argv[2])
    print(check_valid_word(input_word, values_list))
main()
