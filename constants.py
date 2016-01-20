import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.join(BASE_DIR, 'repos')
FACEBOOK_SDK_REPO = 'facebook-sdk'
BOTO3_REPO = 'boto3'
BOTO_REPO = 'boto'
CSV_ROOT = os.path.join(BASE_DIR, 'fixcache', 'analysis_output')
