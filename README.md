# Script for processing 24h ECG recording

## How to run

### Setup
```
virtualenv -p python3.7 env && . env/bin/activate
pip install -r requirements.txt
```

### Run
```
python3 process-ecg-recording.py [-h] --start START --record RECORD [--pdf]

Report from 24h ECG

optional arguments:
  -h, --help       show this help message and exit
  --start START    start of the ECG recording in yyyy-mm-dd hh:mm:ss format
  --record RECORD  file with ECG recording in CSV format
  --pdf            output report in a pdf-file
```
