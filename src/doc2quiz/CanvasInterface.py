#!/usr/bin/env python3
import os
import requests
from canvasapi import Canvas
from time import sleep
from prettytable import PrettyTable


class CanvasInterface:
    def __init__(self, api_url, api_key, course_id):
        self.api_url = api_url
        self.api_key = api_key
        self.course_id = course_id
        self.canvas = Canvas(self.api_url, self.api_key)

    def check_progress(self, progress_url):
        """Poll the progress URL and check the current state of the migration."""
        while True:
            response = requests.get(progress_url)
            progress_data = response.json()

            if progress_data.get('status') == 'unauthenticated':
                print("API key not authorized for progress REST calls.")
                return

            # Safely get the workflow_state from progress_data
            current_state = progress_data.get('workflow_state', 'unknown')

            print(f"Current migration state: {current_state}")

            # Check if migration is completed or failed
            if current_state == 'completed':
                print("Quiz import completed successfully.")
                break
            elif current_state == 'failed':
                print(f"Quiz import failed: {progress_data}")
                break
            elif current_state == 'queued':
                print("Quiz import is still queued. Waiting...")
            else:
                print(f"Progress: {progress_data.get('completion', 0)}%")

            sleep(5)  # Wait before polling again

    def upload_qti_file(self, qti_file_path):
        try:
            # Step 1: Create a content migration with a pre_attachment for the QTI file
            file_name = os.path.basename(qti_file_path)
            file_size = os.path.getsize(qti_file_path)

            print("Step 1: Creating content migration with pre_attachment...")

            course = self.canvas.get_course(self.course_id)
            # Create the content migration (preparing for file upload)
            content_migration = course.create_content_migration(
                migration_type="qti_converter",  # Use the correct migration type
                pre_attachment={
                    "name": file_name,
                    "size": file_size,
                }
            )

            # Extract pre_attachment info for file upload
            upload_info = content_migration.pre_attachment
            upload_url = upload_info["upload_url"]
            upload_params = upload_info["upload_params"]

            # print(f"Pre_attachment info received. Uploading file to {upload_url}...")

            # Step 2: Upload the file using the upload URL and parameters
            with open(qti_file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(upload_url, data=upload_params, files=files)

            if response.status_code != 201:
                raise Exception(f"File upload failed: {response.text}")

            print("File uploaded successfully.")

            # Step 3: Get content migration to track progress
            print("Step 3: Checking content migration status...")
            content_migration = course.get_content_migration(content_migration.id)

            progress_url = content_migration.progress_url
            print(f"Progress URL: {progress_url}")

            # Step 4: Monitor the progress using progress_url
            print("Step 4: Monitoring the quiz import progress...")

            self.check_progress(progress_url)

        except Exception as e:
            print(f"An error occurred: {e}")

    def list_all_quizzes(self):
        """List all quizzes and display their version number and title in a table."""
        try:
            course = self.canvas.get_course(self.course_id)
            quizzes = course.get_quizzes()

            # Create a table using PrettyTable
            table = PrettyTable()
            table.field_names = ["Version", "Quiz Title"]

            # Iterate through each quiz and add its version number and title to the table
            for quiz in quizzes:
                table.add_row([quiz.version_number, quiz.title])

            # Print the table
            print(table)

        except Exception as e:
            print(f"An error occurred while retrieving quizzes: {e}")


def upload_canvas_quiz(qti_file_path):
    api_url = os.getenv("CANVAS_API_URL", 'https://canvas.instructure.com/')
    api_key = os.getenv("CANVAS_API_KEY")
    course_id = os.getenv("CANVAS_COURSE_ID")

    if not api_key or not course_id:
        print("Missing API key or course ID. Please set the environment variables.")
    else:
        # Instantiate the CanvasInterface class and call the upload_qti_file method
        canvas_interface = CanvasInterface(api_url, api_key, course_id)
        canvas_interface.upload_qti_file(qti_file_path)
        canvas_interface.list_all_quizzes()


if __name__ == "__main__":
    # Get environment variables
    upload_canvas_quiz("outputs/xml.zip")
