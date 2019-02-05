#!/usr/bin/env python

"""
Convert a NumPy archive file to separate text files.

Author: Herman Kamper, Ewald van der Westhuizen
Contact: kamperh@gmail.com, ewaldvdw@gmail.com
Date: 2019
"""

from os import path
from tqdm import tqdm
import argparse
import numpy as np
import os
import sys

#-----------------------------------------------------------------------------#
#                              UTILITY FUNCTIONS                              #
#-----------------------------------------------------------------------------#

def check_argv():
    """Check the command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__.strip().split("\n")[0], add_help=False
        )
    parser.add_argument("--strip_vads", type=bool, default=True, help="Set the to False to keep the VAD indices in the output file names or True to strip them or True to strip them. Default is True (strip VAD indices).")
    parser.add_argument("npz_fn", type=str, help="NumPy archive")
    parser.add_argument(
        "output_dir", type=str,
        help="directory where binary files are written (is created if "
        "it doesn't exist"
        )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


#-----------------------------------------------------------------------------#
#                                MAIN FUNCTION                                #
#-----------------------------------------------------------------------------#

def main():
    args = check_argv()

    print("Reading:", args.npz_fn)
    feat_dict = np.load(args.npz_fn)

    if not path.isdir(args.output_dir):
        os.makedirs(args.output_dir)

    print("Writing to:", args.output_dir)
    for utt_key in tqdm(sorted(feat_dict)):

        if args.strip_vads:
            outfn = ''.join(utt_key.rpartition('_')[0:-2])
        else:
            outfn = utt_key

        fn = path.join(args.output_dir, outfn + ".txt")
        np.savetxt(fn, feat_dict[utt_key])

if __name__ == "__main__":
    main()