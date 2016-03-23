"""Constants."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.join(BASE_DIR, 'repos')
FACEBOOK_SDK_REPO = 'facebook-sdk'
BOTO3_REPO = 'boto3'
BOTO_REPO = 'boto'
RASPBERRYIO_REPO = 'raspberryio'
AML = 'awesome-machine-learning'
CSV_ROOT = os.path.join(BASE_DIR, 'fixcache', 'analysis_output')
LOGFILE = os.path.join(BASE_DIR, 'fixcache', 'logs', 'fixcache2.log')
CURRENT_VERSION = 'version_5'

REPO_DICT = {
    'facebook-sdk': FACEBOOK_SDK_REPO,
    'boto3': BOTO3_REPO,
    'boto': BOTO_REPO,
    'raspberryio': RASPBERRYIO_REPO
}

REPO_DATA = {
    'facebook-sdk': {
        'color': 'blue',
        'legend': 'facebook-sdk.git (#c=346)',
        'commit_num': 346
    },
    'boto': {
        'color': 'orange',
        'legend': 'boto.git (#c=6935)',
        'commit_num': 6935
    },
    'boto3': {
        'color': 'red',
        'legend': 'boto3.git (#c=685)',
        'commit_num': 685
    },
    'raspberryio': {
        'color': 'green',
        'legend': 'raspberryio.git (#c=614)',
        'commit_num': 614
    }
}

version_color = {
    'version_1': 'red',
    'version_2': 'blue',
    'version_3': 'orange',
    'version_4': 'green',
    'version_5': 'yellow'
}
