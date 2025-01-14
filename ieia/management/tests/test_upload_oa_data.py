"""
Tests for management command that uploads submission/assessment data.
"""


import tarfile
from io import BytesIO
from urllib.parse import urlparse


import boto3
import moto
from submissions import api as sub_api
from ieia.management.commands import upload_oa_data
from ieia.test_utils import CacheResetTest
from ieia.workflow import api as workflow_api


class UploadDataTest(CacheResetTest):
    """
    Test the upload management command.  Archiving and upload are in-scope,
    but the contents of the generated CSV files are tested elsewhere.
    """

    COURSE_ID = "TɘꙅT ↄoUᴙꙅɘ"
    BUCKET_NAME = "com.example.data"
    CSV_NAMES = [
        "assessment.csv", "assessment_part.csv",
        "assessment_feedback.csv", "assessment_feedback_option.csv",
        "submission.csv", "score.csv",
    ]

    @moto.mock_s3
    def test_upload(self):
        # Create an S3 bucket using the fake S3 implementation
        conn = boto3.client("s3")
        conn.create_bucket(Bucket=self.BUCKET_NAME)

        # Create some submissions to ensure that we cover
        # the progress indicator code.
        for index in range(50):
            student_item = {
                'student_id': f"test_user_{index}",
                'course_id': self.COURSE_ID,
                'item_id': 'test_item',
                'item_type': 'ieia',
            }
            submission_text = f"test submission {index}"
            submission = sub_api.create_submission(student_item, submission_text)
            workflow_api.create_workflow(submission['uuid'], ['peer', 'self'])

        # Create and upload the archive of CSV files
        # This should generate the files even though
        # we don't have any data available.
        cmd = upload_oa_data.Command()
        cmd.handle(self.COURSE_ID.encode('utf-8'), self.BUCKET_NAME)

        # Retrieve the uploaded file from the fake S3 implementation
        self.assertEqual(len(cmd.history), 1)
        bucket = conn.list_buckets()["Buckets"][0]["Name"]
        key = conn.list_objects(Bucket=bucket)["Contents"][0]["Key"]
        contents = BytesIO(conn.get_object(
            Bucket=self.BUCKET_NAME,
            Key=key
        )["Body"].read())

        # Expect that the contents contain all the expected CSV files
        with tarfile.open(mode="r:gz", fileobj=contents) as tar:
            file_sizes = {
                member.name: member.size
                for member in tar.getmembers()
            }
            for csv_name in self.CSV_NAMES:
                self.assertIn(csv_name, file_sizes)
                self.assertGreater(file_sizes[csv_name], 0)

        # Expect that we generated a URL for the bucket
        url = cmd.history[0]['url']
        parsed_url = urlparse(url)
        self.assertEqual("https", parsed_url.scheme)
        self.assertIn(
            parsed_url.netloc,
            ["s3.eu-west-1.amazonaws.com", "s3.amazonaws.com"]
        )
        self.assertIn(f"/{self.BUCKET_NAME}", parsed_url.path)
