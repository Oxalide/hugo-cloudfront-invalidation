#!/usr/bin/python
#
# Copyright 2017 Oxalide
# Licensed under MIT

## modules
import sys, re, boto3, time, argparse
from botocore.exceptions import ClientError

## vars
urls = []

## main

print "Purge CloudFront from Hugo New Or Modified Content\n"

# parse distribution ID from argument
parser = argparse.ArgumentParser(description='Push invalidation request to CloudFront')
parser.add_argument('distributionId', metavar='ID', type=str, help='Target distribution ID')
args = parser.parse_args()
print "DistributionID: "+ args.distributionId +"\n"

# for each line from stdin, rewrite the correct path regarding the final URL
for line in sys.stdin:

    if not line: break # quit switch

    # ignore change of files used for building static content
    excludes = [
        re.compile('^(\..*)$'),
        re.compile('(.*\.toml)$'),
        re.compile('(archetypes/.*)'),
        re.compile('(data/.*)'),
        re.compile('(themes/.*/layouts/.*)'),
        re.compile('(themes/.*/archetypes/.*)'),
        re.compile('(themes/.*\.md)$'),
    ]
    if any(regex.match(line) for regex in excludes):
        continue

    # match and format purge url
    content = re.compile('^(content/)+')
    static = re.compile('^(static/)+')
    theme = re.compile('^(themes/hyde)(.*)+')

    if content.match(line):
        urls.append("/post/"+ re.search("^(content/post/)(.*)(\.md)$",line).group(2) +"/index.html")

    if static.match(line):
        urls.append("/post/"+
            re.search("^(static/post/)(.*)/(.*)$",line).group(2)
            +"/"+
            re.search("^(static/post/)(.*)/(.*)$",line).group(3)
        )

    if theme.match(line):
        urls.append("/"+ re.search("^(themes/hyde/)(.*)$",line).group(2))

# no change
if len(urls) == 0:
    print "Nothing to do !"
    exit(0)

# if there are change
else:
    print "Objects to invalidate:"
    for url in urls:
        print "\t"+ url
    print

    # connect to AWS and push invalidation request
    try:
        client = boto3.client('cloudfront')
        response = client.create_invalidation(
            DistributionId=args.distributionId,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(urls),
                    'Items': urls
                    },
                'CallerReference': str(time.time())
            }
        )

        print "Status: "+ response['Invalidation']['Status'] +"\n"
        exit(0)

    except ClientError as e:
        print "Unexpected error: %s\n" % e
        exit(1)
