from . import log


def get_column_sizes(rows):
    # Calculate column size
    csizes = list()
    for column_items in zip(*rows):
        clargest = max(len(log.ANSI_ESCAPE.sub('', t)) for t in column_items)
        # Set to be at least n character in length
        # Otherwise, round up to closest multiple of 4
        if clargest < 12:
            csizes.append(12)
        else:
            csize = clargest + (4 - clargest % 4)
            csizes.append(csize)
    return csizes
