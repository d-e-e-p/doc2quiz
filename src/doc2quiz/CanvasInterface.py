#!/usr/bin/env python3
import os
import sys
import requests
from canvasapi import Canvas
from time import sleep
from prettytable import PrettyTable


class CanvasInterface:
    def __init__(self):
        self.api_url = os.getenv("CANVAS_API_URL", 'https://canvas.instructure.com/')
        self.api_key = os.getenv("CANVAS_API_KEY")
        self.course_id = os.getenv("CANVAS_COURSE_ID")
        self.check_env()
        self.canvas = Canvas(self.api_url, self.api_key)

    def check_env(self):
        if not self.api_key:
            print("Missing CANVAS_API_KEY environment variable")
            sys.exit(1)
        if not self.course_id:
            print("Missing CANVAS_COURSE_ID environment variable")
            sys.exit(1)

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

    def upload_qti_file(self, file_path):
        try:
            # Step 1: Create a content migration with a pre_attachment for the QTI file
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

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
            with open(file_path, 'rb') as file:
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

    def upload_img_file(self, file_path):
        try:
            # Step 1: Get the course and prepare file info
            file_name = os.path.basename(file_path)

            print("Step 1: Getting course and preparing for file upload...")
            course = self.canvas.get_course(self.course_id)

            # Step 2: Get the destination folder (Uploaded Media) in the course
            print("Step 2: Locating 'Uploaded Media' folder...")
            folders = course.get_folders()
            uploaded_files_folder = None
            for folder in folders:
                if folder.full_name == "course files/Uploaded Media":
                    uploaded_files_folder = folder
                    break

            if not uploaded_files_folder:
                raise Exception("'Uploaded Media' folder not found in the course.")

            # Step 3: Upload the file to the 'Uploaded Media' folder
            print(f"Step 3: Uploading {file_name} to 'Uploaded Media'...")
            with open(file_path, 'rb') as file:
                uploaded_file = uploaded_files_folder.upload(file)

            if not uploaded_file:
                raise Exception(f"File upload failed for {file_name}.")

            print("File uploaded successfully.")
            
            # Step 4: Return uploaded file information
            print(f"Uploaded file details: {uploaded_file}")
            return uploaded_file

        except Exception as e:
            print(f"An error occurred: {e}")

    def upload_img_dir(self, source_dir, root_dir):
        try:
            # Step 1: Get the course
            print("Step 1: Getting course...")
            course = self.canvas.get_course(self.course_id)

            # Step 2: Locate or create the 'Uploaded Media' directory in Canvas
            print("Step 2: Locating 'Uploaded Media' folder...")
            folders = course.get_folders()
            uploaded_media_folder = None
            for folder in folders:
                if folder.full_name == "course files/Uploaded Media":
                    uploaded_media_folder = folder
                    break

            if not uploaded_media_folder:
                raise Exception("'Uploaded Media' folder not found in the course.")

            # Step 3: Create a subfolder under 'Uploaded Media' named after the extension (e.g., 'png')
            print(f"Step 3: Creating/locating 'Uploaded Media/{root_dir}' folder...")
            subfolder_name = f"Uploaded Media/{root_dir}"
            target_folder = None
            for folder in folders:
                if folder.full_name == f"course files/{subfolder_name}":
                    target_folder = folder
                    break

            if not target_folder:
                print(f"Subfolder '{subfolder_name}' not found. Creating it...")
                target_folder = uploaded_media_folder.create_folder(subfolder_name)

            # Step 4: Walk through the source directory and upload all files with the specified extension
            print(f"Step 4: Uploading files from {source_dir} to 'Uploaded Media/{root_dir}'...")
            for root, dirs, files in os.walk(source_dir):
                relative_path = os.path.relpath(root, source_dir)
                current_folder = target_folder

                # Create subdirectories under 'png' in Canvas if needed
                if relative_path != ".":
                    subfolder_path = f"{subfolder_name}/{relative_path}"
                    current_folder = None
                    for folder in folders:
                        if folder.full_name == f"course files/{subfolder_path}":
                            current_folder = folder
                            break

                    if not current_folder:
                        print(f"Creating subfolder '{subfolder_path}'...")
                        current_folder = target_folder.create_folder(relative_path)

                # Upload files
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    print(f"Uploading {file_name} to '{current_folder.full_name}' : ", end="")
                    with open(file_path, 'rb') as file:
                        uploaded_file = current_folder.upload(file)

                    if not uploaded_file:
                        print(f" File upload failed for {file_name}.")
                    else:
                        print(" ok")

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
            table.align["Quiz Title"] = "l"
    
            # Iterate through each quiz and add its version number and title to the table
            for quiz in quizzes:
                table.add_row([quiz.version_number, quiz.title])
    
            # Print the table
            print(table)
    
        except Exception as e:
            print(f"An error occurred while retrieving quizzes: {e}")


def upload_canvas_quiz(qti_file_path):
    canvas_interface = CanvasInterface()
    canvas_interface.upload_qti_file(qti_file_path)
    canvas_interface.list_all_quizzes()


def upload_canvas_images(source_dir, root_dir):
    canvas_interface = CanvasInterface()
    canvas_interface.upload_img_dir(source_dir, root_dir)


if __name__ == "__main__":
    # Get environment variables
    upload_canvas_quiz("outputs/xml.zip")
