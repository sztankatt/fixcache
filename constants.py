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

graph_data = {
    'title': 'Figure 4',
    'curves': [
        {
            'args': ['pythonforfacebook/facebook-sdk.git (#c=346)'],
            'options': {
                'color': 'blue',
                'repo': 'facebook-sdk',
            }
        },
        {
            'args': ['boto/boto.git (#c=6935)'],
            'options': {
                'color': 'orange',
                'repo': 'boto',
            }
        },
        {
            'args': ['boto/boto3.git (#c=685)'],
            'options': {
                'color': 'red',
                'repo': 'boto3',
            }
        },
        {
            'args': ['python/raspberryio.git (#c=614)'],
            'options': {
                'color': 'green',
                'repo': 'raspberryio',
            }
        },
    ]
}
