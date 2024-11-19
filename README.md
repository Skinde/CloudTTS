# Summary
Cloud TTS is a solution to the problem of converting text in a PDF into an audiobook.

It uses a Coqui TTS image on Google Cloud to create multiple Google Cloud Run jobs. These jobs process segments of the PDF text and convert their respective parts into WAV audio files. Finally, the audio segments are stored in a Google Cloud Bucket, downloaded, and merged using Python.

Parallelization, communication, and unification of the final product are managed by a master node running pdfreader2.py.

The user has the option to control:

The number of sentences each job processes.
The names of the respective jobs and files.
However, CLOUDTTS will always attempt to maximize the number of jobs based on the total number of sentences divided by the number of sentences per job. Therefore, there is a limit to the number of pages that can be processed, depending on the number of sentences per job, due to Google Cloud's restrictions on the number of jobs that can be created per minute.

To address this issue, you can either increase the number of sentences per job or limit the number of pages processed per minute.

# Installation
You will need a Google Cloud project, an available bucket, and credentials on your machine. You'll need to provide the project ID, the name of the bucket where data will be stored, specify the name of the PDF file to convert, the number of sentences per page (recommended 5–20), the job name (any unique string), and the pages you want to convert to audio (start and end pages). For details on how to provide the necessary credentials, visit:
[Google Workspace: Create Credentials](https://developers.google.com/workspace/guides/create-credentials)
[Google Cloud: Provide Credentials ADC](https://cloud.google.com/docs/authentication)
To run the master node you will need:

```
pip install -r requirements.txt
python pdfreader2.py
```

