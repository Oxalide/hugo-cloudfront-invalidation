# Hugo CloudFront Invalidation

This script is designed to push invalidation request to CloudFront for your Hugo website.

It use git to track change and format the proper request to submit to CloudFront.

We write this script to purge CloudFront in our Gitlab Pipeline dedicated to publish our site made with Hugo (https://blog.oxalide.io).

# Usage

You need boto3 library from AWS:

    pip install awscli

Because we use this script in our Gitlab pipeline, AWS credential must be provided by environment variable:

    export AWS_SECRET_ACCESS_KEY=xxxx
    export AWS_ACCESS_KEY_ID=xxxx

To use this script, simply go in the root directory of your local copy of Hugo:

    cd xxxx
    git diff --name-only origin/master | python hugo-cf-invalidation.py YOURDISTRIBUTIONID

    Purge CloudFront from Hugo New Or Modified Content

    DistributionID: xxxxxxxxxx

    Objects to invalidate:
	     /post/aws-elb-best-practices/index.html

    Status: InProgress

To use this script in your Gitlab Pipeline remember to provide AWS credential.

## Gitlab CI



# Copyright and license

Code and documentation copyright 2017 Oxalide. Code and documentation released under the MIT license.
