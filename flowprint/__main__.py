import argparse
import json
import numpy as np
import os

from flowprint import FlowPrint
from preprocessor import Preprocessor
from sklearn.model_selection import train_test_split


def fingerprint(flowprint, args):
    """Execute Flowprint in fingerprint mode"""
    ################################################################
    #                      Process input data                      #
    ################################################################
    # Initialise flows and labels
    X, y = list(), list()
    # Initialise preprocessor
    preprocessor = Preprocessor(verbose=True)

    # Parse files - if necessary
    if args.pcaps:
        # Process data
        X_, y_ = preprocessor.process(args.pcaps, args.pcaps)
        # Add data to datapoints
        X.append(X_)
        y.append(y_)

    # Load preprocessed data - if necessary
    if args.read:
        # Loop over all preprocessed files
        for infile in args.read:
            # Load each file
            X_, y_ = preprocessor.load(infile)
            # Add input file to data
            X.append(X_)
            y.append(y_)

    # Concatenate datapoints
    X = np.concatenate(X)
    y = np.concatenate(y)

    # Write preprocessed data - if necessary
    if args.write:
        # Save data
        preprocessor.save(args.write, X, y)

    ################################################################
    #               Split fingerprints if necessary               #
    ################################################################

    if args.split:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.split, random_state=args.random)
        data = [('train', X_train, y_train), ('test', X_test, y_test)]
    else:
        data = [('', X, y)]

    # Loop over both sets
    for type, X, y in data:

        ################################################################
        #                     Create fingerprints                      #
        ################################################################

        # Fit fingerprints
        flowprint.fit(X, y)

        # Make dictionary of label -> fingerprints
        fingerprints = dict()
        # Fill fingerprints
        for fingerprint, label in flowprint.fingerprints.items():
            # Add fingerprints
            fingerprints[label] = fingerprints.get(label, []) + [fingerprint]

        ################################################################
        #                     Output fingerprints                      #
        ################################################################

        # Output to file
        if args.fingerprint:
            # Set output file
            outfile, ext = os.path.splitext(args.fingerprint)
            outfile_ = "{}{}{}".format(outfile, '.' + type if type else type, ext)
            # Transform fingerprints to JSON format
            for label, fps in fingerprints.items():
                # Transform fingerprints to dictionary
                fingerprints[label] = [fp.to_dict() for fp in fps]

            # Dump fingerprints to JSON
            with open(outfile_, 'w') as outfile:
                json.dump(fingerprints, outfile)

            # Notify user fingerprints were saved
            print("Fingerprints saved to {}".format(outfile_))

        # Output to terminal
        else:
            # Select type of fingerprints to output
            print("Output {}fingerprints:".format(type + ' ' if type else type))
            # Output fingerprints
            for label, fingerprint in sorted(fingerprints.items()):
                print("{}:".format(label))
                for fp in sorted(fingerprint):
                    # Get fingerprints as set
                    print("    {}".format(fp))
                print()





def recognition(flowprint, train, test):
    """Execute Flowprint in recognition mode"""
    # TODO cleanup dramatically
    train_fps = dict()
    for k, val in train.items():
        for v in val:
            if v in train_fps:
                train_fps[v] = train_fps[v] + [k]
            else:
                train_fps[v] = [k]

    for k, val in test.items():
        print(k)
        for v in val:
            best_match = None
            best_score = 0
            for fp, label in train_fps.items():
                if v.compare(fp) > best_score:
                    best_score = v.compare(fp)
                    best_match = label
            print("    {} --> {}".format(v, best_match))
    raise ValueError("Warning, should be implemented properly")

def detection(flowprint, train, test):
    """Execute Flowprint in detection mode"""
    # TODO cleanup dramatically
    train_fps = dict()
    for k, val in train.items():
        for v in val:
            if v in train_fps:
                train_fps[v] = train_fps[v] + [k]
            else:
                train_fps[v] = [k]

    for k, val in test.items():
        print(k)
        for v in val:
            for fp, label in train_fps.items():
                if v.compare(fp) > 0.1:
                    print("    {} --> {}".format(v, "matches"))
                    break
            else:
                print("    {} --> {}".format(v, "is anomalous"))
        raise ValueError("Warning, should be implemented properly")




if __name__ == "__main__":
    ########################################################################
    #                           Parse arguments                            #
    ########################################################################

    # Create argument parser
    parser = argparse.ArgumentParser(
                prog="flowprint.py",
                description="Flowprint: Semi-Supervised Mobile-App\nFingerprinting on Encrypted Network Traffic",
                formatter_class=argparse.RawTextHelpFormatter)

    # Output arguments
    group_output = parser.add_mutually_exclusive_group(required=False)
    group_output.add_argument('--fingerprint', nargs='?', help="run FlowPrint in raw fingerprint generation mode (default)")
    group_output.add_argument('--detection'  , action='store_true', help="run FlowPrint in unseen app detection mode")
    group_output.add_argument('--recognition', action='store_true', help="run FlowPrint in app recognition mode")

    # FlowPrint parameters
    group_flowprint = parser.add_argument_group("FlowPrint parameters")
    group_flowprint.add_argument('-b', '--batch'      , type=float, default=300, help="batch size in seconds       (default=300)")
    group_flowprint.add_argument('-c', '--correlation', type=float, default=0.1, help="cross-correlation threshold (default=0.1)")
    group_flowprint.add_argument('-s', '--similarity' , type=float, default=0.9, help="similarity threshold        (default=0.9)")
    group_flowprint.add_argument('-w', '--window'     , type=float, default=30 , help="window size in seconds      (default=30)")

    # Flow data input/output agruments
    group_data_in = parser.add_argument_group("Flow data input/output")
    group_data_in.add_argument('-p', '--pcaps' ,             nargs='+' , help="path to pcap(ng) files to run through FlowPrint")
    group_data_in.add_argument('-r', '--read'  ,             nargs='+' , help="read preprocessed data from given files")
    group_data_in.add_argument('-o', '--write' ,                         help="write preprocessed data to given file")
    group_data_in.add_argument('-l', '--split' , type=float, default= 0, help="fraction of data to select for testing (default= 0)")
    group_data_in.add_argument('-a', '--random', type=int  , default=42, help="random state to use for split          (default=42)")

    # Train/test input arguments
    group_data_fps = parser.add_argument_group("Train/test input")
    group_data_fps.add_argument('-t', '--train', nargs='+', help="fingerprints used for training")
    group_data_fps.add_argument('-e', '--test' , nargs='+', help="fingerprints used for testing")

    # Set help message
    parser.format_help = lambda: \
"""usage: {} [-h]
                    (--detection | --fingerprint [FILE] | --recognition)
                    [-b BATCH] [-c CORRELATION], [-s SIMILARITY], [-w WINDOW]
                    [-p PCAPS...] [-rp READ...] [-wp WRITE]

{}

Arguments:
  -h, --help                 show this help message and exit

FlowPrint mode (select up to one):
  --fingerprint [FILE]       run in raw fingerprint generation mode (default)
                             outputs to terminal or json FILE
  --detection                run in unseen app detection mode (Unimplemented)
  --recognition              run in app recognition mode      (Unimplemented)

FlowPrint parameters:
  -b, --batch       FLOAT    batch size in seconds       (default=300)
  -c, --correlation FLOAT    cross-correlation threshold (default=0.1)
  -s, --similarity  FLOAT    similarity threshold        (default=0.9)
  -w, --window      FLOAT    window size in seconds      (default=30)

Flow data input/output (either --pcaps or --read required):
  -p, --pcaps  PATHS...      path to pcap(ng) files to run through FlowPrint
  -r, --read   PATHS...      read preprocessed data from given files
  -o, --write  PATH          write preprocessed data to given file
  -i, --split  FLOAT         fraction of data to select for testing (default= 0)
  -r, --random FLOAT         random state to use for split          (default=42)

Train/test input (for --detection/--recognition):
  -t, --train PATHS...       path to json files containing training fingerprints
  -e, --test  PATHS...       path to json files containing testing fingerprints
""".format(
    # Usage Parameters
    parser.prog,
    # Description
    parser.description)

    # Parse given arguments
    args = parser.parse_args()

    ########################################################################
    #                           Check arguments                            #
    ########################################################################

    # --fingerprint requires --pcaps or --read
    if not args.detection and\
       not args.recognition and\
       not args.pcaps and\
       not args.read:
        # Give help message
        print(parser.format_help())
        # Throw exception
        raise RuntimeError("--recognition requires input data, please specify "
                           "--pcaps or --read arguments.")

    # --detection or --recognition require --train and --test
    if (args.detection or args.recognition) and not (args.train and args.test):
        # Give help message
        print(parser.format_help())
        # Throw exception
        raise RuntimeError("--detection/--recognition require training and "
                           "testing fingerprints, please specify --train and "
                           "--test arguments.")

    ########################################################################
    #                           Create FlowPrint                           #
    ########################################################################

    # Create FlowPrint instance with given arguments
    flowprint = FlowPrint(
        batch       = args.batch,
        window      = args.window,
        correlation = args.correlation,
        similarity  = args.similarity
    )

    ########################################################################
    #                             Execute mode                             #
    ########################################################################
    # Fingerprint mode
    if not args.detection and not args.recognition:
        fingerprint(flowprint, args)
    # Detection/Recognition mode
    else:

        ################################################################
        #                      Load fingerprints                       #
        ################################################################
        # Load train and test fingerprints
        train_fps = dict()
        test_fps  = dict()

        from fingerprint import Fingerprint

        # Loop over training fingerprint files
        for train in args.train:
            # Read fingerprints
            with open(train) as infile:
                # Read fingerprints
                data = json.load(infile)
                # Loop over fingerprints
                for label, fingerprints in data.items():
                    # Transform data to fingerprints
                    fps = set([Fingerprint().from_dict(fp) for fp in fingerprints])
                    # Update training fingerprints
                    train_fps[label] = train_fps.get(label, set()) | fps

        # Loop over training fingerprint files
        for test in args.test:
            # Read fingerprints
            with open(test) as infile:
                # Read fingerprints
                data = json.load(infile)
                # Loop over fingerprints
                for label, fingerprints in data.items():
                    # Transform data to fingerprints
                    fps = set([Fingerprint().from_dict(fp) for fp in fingerprints])
                    # Update training fingerprints
                    test_fps[label] = test_fps.get(label, set()) | fps

        ################################################################
        #                         Execute mode                         #
        ################################################################
        # Detection mode
        if args.detection:
            detection(flowprint, train_fps, test_fps)
        # Recognition mode
        elif args.recognition:
            recognition(flowprint, train_fps, test_fps)