#!/usr/bin/env python3
import os
import sys
import requests
import logging
from canvasapi import Canvas
from time import sleep
from prettytable import PrettyTable
# from natsort import natsorted

log = logging.getLogger()


class CanvasInterface:
    def __init__(self):
        self.api_url = os.getenv("CANVAS_API_URL", 'https://canvas.instructure.com/')
        self.api_key = os.getenv("CANVAS_API_KEY")
        self.course_id = os.getenv("CANVAS_COURSE_ID")
        self.check_env()
        self.canvas = Canvas(self.api_url, self.api_key)
        self.check_authorization()

    def check_env(self):
        if not self.api_key:
            log.error("Missing CANVAS_API_KEY environment variable")
            sys.exit(1)
        if not self.course_id:
            log.error("Missing CANVAS_COURSE_ID environment variable")
            sys.exit(1)

    def check_authorization(self):
        try:
            # Try to get the current user to check if the API key is authorized
            user = self.canvas.get_user('self')
            log.error(f"Canvas API Key is authorized. Current user: {user}")
            return True
        except Exception as e:
            log.error(f"Authorization failed: {e}")
            return False

    def check_progress(self, progress_url):
        """Poll the progress URL and check the current state of the migration."""
        while True:
            response = requests.get(progress_url)
            progress_data = response.json()

            if progress_data.get('status') == 'unauthenticated':
                log.error("API key not authorized for progress REST calls.")
                return

            # Safely get the workflow_state from progress_data
            current_state = progress_data.get('workflow_state', 'unknown')

            log.info(f"Current migration state: {current_state}")

            # Check if migration is completed or failed
            if current_state == 'completed':
                log.info("Quiz import completed successfully.")
                break
            elif current_state == 'failed':
                log.warning(f"Quiz import failed: {progress_data}")
                break
            elif current_state == 'queued':
                log.info("Quiz import is still queued. Waiting...")
            else:
                log.info(f"Progress: {progress_data.get('completion', 0)}%")

            sleep(5)  # Wait before polling again

    def upload_qti_file(self, file_path):
        try:
            # Step 1: Create a content migration with a pre_attachment for the QTI file
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            log.info("Step 1: Creating content migration with pre_attachment...")

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

            # log.info(f"Pre_attachment info received. Uploading file to {upload_url}...")

            # Step 2: Upload the file using the upload URL and parameters
            with open(file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(upload_url, data=upload_params, files=files)

            if response.status_code != 201:
                raise Exception(f"File upload failed: {response.text}")

            log.info("File uploaded successfully.")

            # Step 3: Get content migration to track progress
            log.info("Step 3: Checking content migration status...")
            content_migration = course.get_content_migration(content_migration.id)

            progress_url = content_migration.progress_url
            log.info(f"Progress URL: {progress_url}")

            # Step 4: Monitor the progress using progress_url
            log.info("Step 4: Monitoring the quiz import progress...")

            self.check_progress(progress_url)

        except Exception as e:
            log.error(f"An error occurred: {e}")

    def upload_img_file(self, file_path):
        try:
            # Step 1: Get the course and prepare file info
            file_name = os.path.basename(file_path)

            log.info("Step 1: Getting course and preparing for file upload...")
            # course = self.canvas.get_course(self.course_id)

            # Step 2: Get the destination folder (Uploaded Media) in the course
            log.info("Step 2: Locating 'Uploaded Media' folder...")
            uploaded_media_folder = self.get_uploaded_media_folder()

            # Step 3: Upload the file to the 'Uploaded Media' folder
            log.info(f"Step 3: Uploading {file_name} to 'Uploaded Media'...")
            with open(file_path, 'rb') as file:
                uploaded_file = uploaded_media_folder.upload(file)

            if not uploaded_file:
                raise Exception(f"File upload failed for {file_name}.")

            log.info("File uploaded successfully.")
            
            # Step 4: Return uploaded file information
            log.info(f"Uploaded file details: {uploaded_file}")
            return uploaded_file

        except Exception as e:
            log.error(f"An error occurred: {e}")

    def get_uploaded_media_folder(self):

        course = self.canvas.get_course(self.course_id)
        folders = course.get_folders()

        uploaded_media_folder = next((f for f in folders if f.full_name == "course files/Uploaded Media"), None)
        if not uploaded_media_folder:

            parent_folder = next((f for f in folders if f.full_name == "course files"), None)

            if parent_folder:

                uploaded_media_folder = course.create_folder(name='Uploaded Media', parent_folder_id=parent_folder.id)
                log.info(f"Folder 'Uploaded Media' created with ID: {uploaded_media_folder.id}")
            else:
                log.error("Error: Could not locate the 'course files' parent folder.")

        if not uploaded_media_folder:
            raise Exception("'Uploaded Media' folder not found in the course.")

        return uploaded_media_folder

    def upload_zipfile(self, zipfile):
        try:
            # Step 1: Get the course
            log.info("Step 1: Getting course...")
            course = self.canvas.get_course(self.course_id)
            # available_migrators = course.get_migrators()

            # Step 2: Locate or create the 'Uploaded Media' directory in Canvas
            log.info("Step 2: Locating 'Uploaded Media' folder...")
            uploaded_media_folder = self.get_uploaded_media_folder()

            # Step 3: Create a zip with a pre_attachment
            file_name = os.path.basename(zipfile)
            file_size = os.path.getsize(zipfile)

            # Upload png*zip files
            content_migration = course.create_content_migration(
                migration_type="zip_file_importer",
                pre_attachment={
                    "name": file_name,
                    "size": file_size,
                    "content_type": "application/zip",
                },
                settings={
                    "folder_id": uploaded_media_folder.id
                }
            )

            # Extract pre_attachment info for file upload
            upload_info = content_migration.pre_attachment
            upload_url = upload_info["upload_url"]
            upload_params = upload_info["upload_params"]

            # log.info(f"Pre_attachment info received. Uploading file to {upload_url}...")

            # Step 2: Upload the file using the upload URL and parameters
            with open(zipfile, 'rb') as file:
                files = {'file': file}
                response = requests.post(upload_url, data=upload_params, files=files)

            if response.status_code != 201:
                raise Exception(f"File upload failed: {response.text}")

            log.info("File uploaded successfully.")

            # Step 3: Get content migration to track progress
            log.info("Step 3: Checking content migration status...")
            content_migration = course.get_content_migration(content_migration.id)

            progress_url = content_migration.progress_url
            log.info(f"Progress URL: {progress_url}")

            # Step 4: Monitor the progress using progress_url
            log.info("Step 4: Monitoring the quiz import progress...")

            self.check_progress(progress_url)

        except Exception as e:
            log.error(f"An error occurred: {e}")

    def update_quizzes(self, allowed_attempts=None, publish=None, unpublish=None):

        log.info(" BEFORE: \n")
        self.list_all_quizzes()

        course = self.canvas.get_course(self.course_id)
        quizzes = course.get_quizzes()
        for quiz in quizzes:
            if allowed_attempts is not None:
                quiz.allowed_attempts = allowed_attempts
            if publish is not None:
                quiz.published = True
            if unpublish is not None:
                quiz.published = False

        log.info(" AFTER: \n")
        self.list_all_quizzes()

    def delete_all_quizzes(self):
        self.list_all_quizzes()
        confirmation = input("Are you sure you want to delete all these quizzes? (y/n): ").strip().lower()
        if confirmation == 'y':
            course = self.canvas.get_course(self.course_id)
            quizzes = course.get_quizzes()
            for quiz in quizzes:
                quiz.delete()
                log.info(f"Deleted quiz: {quiz.title}")

            self.list_all_quizzes()

    def list_all_quizzes(self):
        """List all quizzes and display their version number and title in a table."""
        try:
            course = self.canvas.get_course(self.course_id)
            quizzes = course.get_quizzes()
    
            # Create a table using PrettyTable
            table = PrettyTable()
            table.title = f"{course.name} ({course.id})"
            table.field_names = ["Version", "Published?", "Attempts", "Quiz Title"]
            table.align["Quiz Title"] = "l"
    
            # Iterate through each quiz and add its version number and title to the table
            for quiz in quizzes:
                table.add_row([quiz.version_number, quiz.published, quiz.allowed_attempts, quiz.title])
    
            # Print the table
            log.info(table)
    
        except Exception as e:
            log.error(f"An error occurred while retrieving quizzes: {e}")


def upload_canvas_quiz(qti_file_path):
    canvas_interface = CanvasInterface()
    canvas_interface.upload_qti_file(qti_file_path)
    canvas_interface.list_all_quizzes()


def upload_canvas_images(source_dir, root_dir):
    canvas_interface = CanvasInterface()
    canvas_interface.upload_img_dir(source_dir, root_dir)


def upload_canvas_zipfiles(zipfile):
    canvas_interface = CanvasInterface()
    canvas_interface.upload_zipfile(zipfile)


if __name__ == "__main__":
    # Get environment variables
    upload_canvas_zipfiles("outputs/xml.zip")
