import re


def camelize(thing):
    return re.sub("_(.)", lambda x:x.group(1).upper(), thing)
