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
parser.add_argument('--stsrole', dest='stsrole', type=str, default='0', help='ARN for sts:assmerole')
parser.add_argument('--prefix', dest='urlprefix', type=str, default='', help='Prefix URL with a string, ex: for /draft/index.html, prefix need to be "/draft"')

args = parser.parse_args()
print "DistributionID: "+ args.distributionId +"\n"

urlprefix = args.urlprefix if (args.urlprefix != "" ) else ""

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
        urls.append(urlprefix +"/post/"+ re.search("^(content/post/)(.*)(\.md)$",line).group(2) +"/")
        urls.append(urlprefix +"/post/"+ re.search("^(content/post/)(.*)(\.md)$",line).group(2) +"/index.html")

    if static.match(line):
        urls.append(urlprefix +"/post/"+
            re.search("^(static/post/)(.*)/(.*)$",line).group(2)
            +"/"+
            re.search("^(static/post/)(.*)/(.*)$",line).group(3)
        )

    if theme.match(line):
        urls.append(urlprefix +"/"+ re.search("^(themes/hyde/)(.*)$",line).group(2))

# no change
if len(urls) == 0:
    print "Nothing to do !"
    exit(0)

# if there are change
else:

    # also purge this objects if there is at leat a change on the site
    urls.append(urlprefix +"/")
    urls.append(urlprefix +"/index.html")
    urls.append(urlprefix +"/index.xml")
    urls.append(urlprefix +"/sitemap.xml")

    print "Objects to invalidate:"
    for url in urls:
        print "\t"+ url
    print

    # connect to AWS and push invalidation request
    try:

        # use sts:assumerole if provided
        if args.stsrole != '0':

            # assume role
            print "Use sts:assumerole => "+ args.stsrole + "\n"
            sts_client = boto3.client('sts')
            assumedRoleObject = sts_client.assume_role(
                RoleArn=args.stsrole,
                RoleSessionName="AssumeRoleHugoCFInvalidation"
            )

            # use new credentials to connect to cloudfront
            client = boto3.client(
                'cloudfront',
                aws_access_key_id=assumedRoleObject['Credentials']['AccessKeyId'],
                aws_secret_access_key=assumedRoleObject['Credentials']['SecretAccessKey'],
                aws_session_token=assumedRoleObject['Credentials']['SessionToken'],
            )

        else:
            # use "default" credentials to connect to cloudfront
            client = boto3.client('cloudfront')

        # push invalidation request to cloudfront
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

        print "Invalidation status: "+ response['Invalidation']['Status'] +"\n"
        exit(0)

    except ClientError as e:
        print "Unexpected error: %s\n" % e
        exit(1)
