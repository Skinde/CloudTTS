from google.cloud import run_v2
from PyPDF2 import PdfReader
from spellchecker import SpellChecker
from google.cloud.storage.client import Client
from pydub import AudioSegment
import enchant
import os
import re
import time


def split_and_group_by_sentences(text, n):
    print("Splitting text into jobs...")
    # Step 1: Split the text into sentences based on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    
    # Step 2: Group sentences into chunks of 'n'
    grouped_sentences = [
        ' '.join(sentences[i:i+n]) for i in range(0, len(sentences), n)
    ]
    
    return grouped_sentences


class pdf_reader:
    #------------------------------------------------------------
    #User variables
    #Path to the pdf
    filename = None
    #Number of pages
    pages = None
    #Voice
    jobname = None
    #ProjectID
    projectid = None
    #Max length of a string by words in a job
    maxnumberofsentencespertask = None
    #Numberofparalleljobs
    numberofparalleltasks = None
    #Bucketname
    bucketname = None
    #Client reference
    client = run_v2.JobsClient()
    #Total sent jobs 
    totalsentjobs = 0
    #Completed jobs (for tracking jobs)
    completed_jobs = 0

    region = 'us-central1'
    #------------------------------------------------------------

    def load_json_data(self, json_data):
        self.filename = json_data['filename']
        self.pages = json_data['pages']
        self.jobname = json_data['jobname']
        self.projectid = json_data['projectid']
        self.maxnumberofsentencespertask = json_data['maxnumberofsentencespertask']
        self.numberofparalleltasks = json_data['numberofparalleljobs']
        self.bucketname = json_data['bucketname']
    
    def send_batch(self, containers_list, job_number):
        project_id = self.projectid
        region = "us-central1"
        job_name = self.jobname
        image = "us-central1-docker.pkg.dev/" + project_id + "/ttsimage/coquitts"
        bucket_name = self.bucketname

        
        
        parent = f"projects/{project_id}/locations/{region}"
         # Define the job specification
        job = run_v2.Job(
            template=run_v2.ExecutionTemplate(
                task_count=self.numberofparalleltasks,
                template = run_v2.TaskTemplate(
                    containers=containers_list,
                    volumes=[run_v2.Volume(
                        name="output-volume",
                        gcs=run_v2.GCSVolumeSource(bucket=bucket_name)
                    )]
                )
            )
        )

        request = run_v2.CreateJobRequest(
            parent=parent,
            job = job,
            job_id = job_name + str(job_number)
        )

        operation = self.client.create_job(request=request)

        request = run_v2.RunJobRequest(
            name=parent+"/jobs/"+job_name+str(job_number)
        )

        time.sleep(1)
        self.client.run_job(request=request)


    def create_cloud_run_job(self, text):
        """
        Create a Cloud Run Job using the Google Cloud Client Library.

        :param text: Text to process.
        :param part_id: Part ID for naming output.
        """

        project_id = self.projectid
        region = "us-central1"
        job_name = self.jobname
        image = "us-central1-docker.pkg.dev/" + project_id + "/ttsimage/coquitts"
        bucket_name = self.bucketname

        
        
        parent = f"projects/{project_id}/locations/{region}"
        
        print("Sending jobs...")
        containers_list = []
        for index, text_part in enumerate(text, start=1):
            new_container = run_v2.Container(
                        image=image,
                        args=[ f"--text={text_part}",f"--out_path=/root/tts-output/part{index}.wav","--model_name=tts_models/en/ljspeech/vits",],
                        volume_mounts=[run_v2.VolumeMount(name="output-volume", mount_path="/root/tts-output")],
                        resources=run_v2.ResourceRequirements(limits={"memory": "2Gi", "cpu": "1"})
                    )
            
            containers_list.append(new_container)
            self.send_batch(containers_list, index)
            containers_list = []
        #Once all jobs are sent, wait for them to finish

    def wait_for_jobs(self, text):
         print("Waiting to download all parts...")
         parent = f"projects/{self.projectid}/locations/{self.region}"
         for i in range(1, len(text)):
            try:
                job = self.client.get_job(name=parent+"/jobs/"+self.jobname+str(i))
                status = job.latest_created_execution.completion_status
                print("next job")
                while status != 1:
                    print("waiting on job")
                    job = self.client.get_job(name=parent+"/jobs/"+self.jobname+str(i))
                    status = job.latest_created_execution.completion_status
                    time.sleep(10)
            except Exception as e:
                print(f"an error ocurred {e}")
                return f"Error fetching job status: {e}"
            
    def download_all_parts(self, text):
        Storageclient = Client(project=self.projectid)
        bucket = Storageclient.get_bucket(self.bucketname)
        for i in range(1, len(text)):
            next_file = bucket.get_blob(f"part{i}.wav")
            os.makedirs("./parts", exist_ok=True) 
            next_file.download_to_filename(f"./parts/part{i}.wav")
    
    def combine_all_parts(self, text):
        print("Joining audio segments together... ")
        generated_file = "AudioBook.wav"
        path_to_files = "./parts/"
        combined = None
        for i in range(1,len(text)):
            new_file = AudioSegment.from_wav(path_to_files+f"/part{i}.wav")
            if combined == None:
                combined = new_file
            else:
                combined += new_file
        file_handle = combined.export(f"./{generated_file}", format="wav")
        

    def read(self):
        print("Reading pdf")
        pdf = PdfReader(self.filename)
        text = ""

        for page in pdf.pages[self.pages[0]:self.pages[1]]:
            text = text + page.extract_text()


        temp = text.split()
        spell = SpellChecker()

        print("Checking for conversion errors...")
        #Spell check PDF errors
        i = 0
        for i in range(len(temp)):
            corrected_word = temp[i]
            for c in temp[i]:
                if c == '~':
                    corrected_word = spell.correction(temp[i])
            temp[i] = corrected_word


        d = enchant.Dict("en_US")

        #Remove Soft Hypens
        i = 0
        ln = len(temp) - 1
        while i < ln:
            if temp[i].find('\xad') or temp[i].find('\u00ad') or temp[i].find('\N{SOFT HYPHEN}'):
                temp[i] = temp[i].replace('\xad', '')
                temp[i] = temp[i].replace('\u00ad', '')
                temp[i] = temp[i].replace('\N{SOFT HYPHEN}', '')
                if d.check(temp[i] + temp[i+1]):
                    temp[i] = temp[i] + temp[i+1]
                    temp.pop(i+1)
                    ln -= 1
            i = i + 1

        text = ""
        for word in temp:
            text = text + word
            text = text + " "
        text = text[:-1]

        text = split_and_group_by_sentences(text, self.maxnumberofsentencespertask)
        self.create_cloud_run_job(text)
        self.wait_for_jobs(text)
        self.download_all_parts(text)
        self.combine_all_parts(text)


the_pdf_reader_object = pdf_reader()   

the_pdf_reader_object.filename = input("filename: ")
the_pdf_reader_object.pages = [int(input("pages start: ")), int(input("pages end: "))]
the_pdf_reader_object.jobname = input("jobname: ")
the_pdf_reader_object.projectid = input("projectid: ")
the_pdf_reader_object.maxnumberofsentencespertask = int(input("Max number of words per job: "))
the_pdf_reader_object.numberofparalleltasks = 1 #Leave at 1
the_pdf_reader_object.bucketname = input("bucketname: ")

the_pdf_reader_object.read()




