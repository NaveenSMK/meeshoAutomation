import os
import smtplib
import glob
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import time
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


class emailManager:
    """
    Robot Framework library for automated PDF email management.

    This library provides a single main keyword for processing PDF downloads:
    finding the latest PDF, sending it via email, and cleaning up the local file.
    """

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        """Initialize the PDF email manager with default settings"""
        self.current_dir = os.getcwd()
        self.default_download_folder = "downloads"
        self.download_path = os.path.join(self.current_dir, self.default_download_folder)

    def _ensure_download_path_exists(self, download_path):
        """
        Internal method to create download directory if it doesn't exist

        Args:
            download_path (str): Path to download directory

        Returns:
            bool: True if path exists or was created successfully
        """
        try:
            if not os.path.exists(download_path):
                os.makedirs(download_path, exist_ok=True)
                BuiltIn().log(f"Created download directory: {download_path}")
            else:
                BuiltIn().log(f"Download directory exists: {download_path}")
            return True
        except Exception as e:
            BuiltIn().log(f"ERROR: Failed to create download directory: {str(e)}", level='ERROR')
            return False

    def _find_latest_pdf(self, download_path):
        """
        Internal method to find the most recent PDF file

        Args:
            download_path (str): Path to search for PDF files

        Returns:
            tuple: (success: bool, pdf_path: str or None, error_message: str or None)
        """
        try:
            # Search for PDF files
            pdf_pattern = os.path.join(download_path, "*.pdf")
            pdf_files = glob.glob(pdf_pattern)

            # Filter to only include actual files (not directories)
            pdf_files = [f for f in pdf_files if os.path.isfile(f)]

            if not pdf_files:
                error_msg = f"No PDF files found in directory: {download_path}"
                BuiltIn().log(f"WARNING: {error_msg}", level='WARN')
                return False, None, error_msg

            # Find the most recently modified PDF
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            file_size = os.path.getsize(latest_pdf)
            file_size_mb = round(file_size / (1024 * 1024), 2)

            BuiltIn().log(f"Found latest PDF: {os.path.basename(latest_pdf)} ({file_size_mb} MB)")
            return True, latest_pdf, None

        except Exception as e:
            error_msg = f"Error finding latest PDF: {str(e)}"
            BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
            return False, None, error_msg

    def _send_pdf_email(self, pdf_path, sender_email, receiver_email, email_passkey):
        """
        Internal method to send PDF via email

        Args:
            pdf_path (str): Path to PDF file
            sender_email (str): Sender's email address
            receiver_email (str): Receiver's email address
            email_passkey (str): Email password/app password

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        SCOPES = [
            "https://www.googleapis.com/auth/gmail.send"
        ]
        try:
            # Validate inputs
            if not all([pdf_path, sender_email, receiver_email, email_passkey]):
                error_msg = "Missing required email parameters"
                BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
                return False, error_msg

            if not os.path.exists(pdf_path):
                error_msg = f"PDF file not found: {pdf_path}"
                BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
                return False, error_msg


            # Create email message
            # service = build('gmail', 'v1', credentials=creds)
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = "Automated PDF Labels"

            # Create email body
            filename = os.path.basename(pdf_path)
            modification_time = time.ctime(os.path.getmtime(pdf_path))

            body = f"""This is an automated email.

PDF Document Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• File Name: {filename}
• Last Modified: {modification_time}

Please find the PDF document attached to this email.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This email was generated automatically. Please do not reply to this email.
"""

            msg.attach(MIMEText(body, 'plain',  'utf-8'))

            # Attach PDF file
            BuiltIn().log("Attaching PDF file to email...")
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'pdf')
                part.set_payload(attachment.read())

                # Encode the attachment in Base64
                encoders.encode_base64(part)

            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)

            # create_message = {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}
            # # Send email
            # message = (service.users().messages().send(userId="me", body=create_message).execute())
            # print(F'sent message to {message} Message Id: {message["id"]}')

            BuiltIn().log("Connecting to SMTP server...")
            # server = smtplib.SMTP_SSL('smtp.gmail.com', 587)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, email_passkey)

            BuiltIn().log("Sending email...")
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            server.quit()

            BuiltIn().log(f"SUCCESS: Email sent successfully to {receiver_email}")
            return True, None

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Email authentication failed: {str(e)}. Check email credentials."
            BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {str(e)}"
            BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
            return False, error_msg

    def _delete_pdf_file(self, pdf_path):
        """
        Internal method to delete PDF file

        Args:
            pdf_path (str): Path to PDF file to delete

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            if not os.path.exists(pdf_path):
                error_msg = f"PDF file not found for deletion: {pdf_path}"
                BuiltIn().log(f"WARNING: {error_msg}", level='WARN')
                return False, error_msg

            filename = os.path.basename(pdf_path)
            os.remove(pdf_path)
            BuiltIn().log(f"SUCCESS: PDF file deleted - {filename}")
            return True, None

        except PermissionError as e:
            error_msg = f"Permission denied deleting file: {str(e)}"
            BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
            return False, error_msg
        except Exception as e:
            error_msg = f"Error deleting PDF file: {str(e)}"
            BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
            return False, error_msg

    @keyword("Process PDF Email Workflow")
    def process_pdf_email_workflow(self, sender_email, receiver_email, email_passkey):
        """
        Main Robot Framework keyword to process PDF email workflow.

        This keyword performs the complete workflow:
        1. Verifies/creates download directory
        2. Finds the latest PDF file
        3. Sends PDF via email
        4. Deletes PDF file after successful email

        Args:
            sender_email (str): Sender's email address
            receiver_email (str): Receiver's email address
            email_passkey (str): Email password or app password

        Returns:
            str: "SUCCESS" if all operations completed successfully, "FAILURE" otherwise

        Example:
            | ${result}= | Process PDF Email Workflow | sender@gmail.com | receiver@company.com | myapppassword |
            | Should Be Equal | ${result} | SUCCESS |
        """

        BuiltIn().log("=" * 80)
        BuiltIn().log("STARTING PDF EMAIL WORKFLOW")
        BuiltIn().log("=" * 80)

        workflow_start_time = time.time()

        try:
            # Step 1: Verify/Create download directory
            BuiltIn().log("STEP 1: Verifying download directory...")
            if not self._ensure_download_path_exists(self.download_path):
                BuiltIn().log("FAILURE: Could not create/access download directory", level='ERROR')
                return "FAILURE"

            # Step 2: Find latest PDF
            BuiltIn().log("STEP 2: Searching for latest PDF file...")
            pdf_found, pdf_path, find_error = self._find_latest_pdf(self.download_path)

            if not pdf_found:
                BuiltIn().log(f"FAILURE: {find_error}", level='ERROR')
                return "FAILURE"

            # Step 3: Send email with PDF attachment
            BuiltIn().log("STEP 3: Sending PDF via email...")
            email_sent, email_error = self._send_pdf_email(pdf_path, sender_email, receiver_email, email_passkey)

            if not email_sent:
                BuiltIn().log(f"FAILURE: Email sending failed - {email_error}", level='ERROR')
                BuiltIn().log("PDF file will NOT be deleted due to email failure", level='WARN')
                return "FAILURE"

            # Step 4: Delete PDF file (only if email was successful)
            BuiltIn().log("STEP 4: Deleting PDF file after successful email...")
            file_deleted, delete_error = self._delete_pdf_file(pdf_path)

            if not file_deleted:
                BuiltIn().log(f"WARNING: File deletion failed - {delete_error}", level='WARN')
                BuiltIn().log("Email was sent successfully, but file cleanup failed", level='WARN')
                # Still return SUCCESS since email was sent (main objective achieved)

            # Calculate workflow duration
            workflow_duration = round(time.time() - workflow_start_time, 2)

            BuiltIn().log("=" * 80)
            BuiltIn().log("PDF EMAIL WORKFLOW COMPLETED SUCCESSFULLY")
            BuiltIn().log(f"Total Duration: {workflow_duration} seconds")
            BuiltIn().log(f"Processed File: {os.path.basename(pdf_path)}")
            BuiltIn().log(f"Sent To: {receiver_email}")
            BuiltIn().log("=" * 80)

            return "SUCCESS"

        except Exception as e:
            workflow_duration = round(time.time() - workflow_start_time, 2)
            error_msg = f"Unexpected error in PDF workflow: {str(e)}"
            BuiltIn().log("=" * 80, level='ERROR')
            BuiltIn().log("PDF EMAIL WORKFLOW FAILED", level='ERROR')
            BuiltIn().log(f"Error: {error_msg}", level='ERROR')
            BuiltIn().log(f"Duration: {workflow_duration} seconds", level='ERROR')
            BuiltIn().log("=" * 80, level='ERROR')
            print(f"Error: {error_msg}")
            return "FAILURE"

    @keyword("Set PDF Download Folder")
    def set_pdf_download_folder(self, folder_name):
        """
        Robot Framework keyword to set the default download folder.

        Args:
            folder_name (str): Name of the download folder (relative to current directory)

        Returns:
            str: "SUCCESS" if folder was set successfully, "FAILURE" otherwise

        Example:
            | ${result}= | Set PDF Download Folder | my_downloads |
            | Should Be Equal | ${result} | SUCCESS |
        """
        try:
            BuiltIn().log(f"Setting download folder to: {folder_name}")

            # Validate folder name
            if not folder_name or folder_name.strip() == "":
                BuiltIn().log("ERROR: Folder name cannot be empty", level='ERROR')
                return "FAILURE"

            # Update download path
            old_path = self.download_path
            self.download_path = os.path.join(self.current_dir, folder_name.strip())

            # Create the directory if it doesn't exist
            if self._ensure_download_path_exists(self.download_path):
                BuiltIn().log(
                    f"SUCCESS: Download folder changed from '{os.path.basename(old_path)}' to '{folder_name}'")
                return "SUCCESS"
            else:
                # Revert to old path if creation failed
                self.download_path = old_path
                BuiltIn().log(f"FAILURE: Could not create/access folder '{folder_name}', reverted to previous setting",
                              level='ERROR')
                return "FAILURE"

        except Exception as e:
            error_msg = f"Error setting download folder: {str(e)}"
            BuiltIn().log(f"ERROR: {error_msg}", level='ERROR')
            return "FAILURE"

    @keyword("Get Current Download Folder")
    def get_current_download_folder(self):
        """
        Robot Framework keyword to get the current download folder path.

        Returns:
            str: Current download folder path

        Example:
            | ${current_folder}= | Get Current Download Folder |
            | Log | Current download folder: ${current_folder} |
        """
        BuiltIn().log(f"Current download folder: {self.download_path}")
        return self.download_path

    @keyword("Check PDF Files Count")
    def check_pdf_files_count(self):
        """
        Robot Framework keyword to check how many PDF files are in the download folder.

        Returns:
            int: Number of PDF files found

        Example:
            | ${count}= | Check PDF Files Count |
            | Should Be True | ${count} > 0 | No PDF files found |
        """
        try:
            if not os.path.exists(self.download_path):
                BuiltIn().log(f"Download folder does not exist: {self.download_path}")
                return 0

            pdf_files = glob.glob(os.path.join(self.download_path, "*.pdf"))
            pdf_files = [f for f in pdf_files if os.path.isfile(f)]
            count = len(pdf_files)

            BuiltIn().log(f"Found {count} PDF files in download folder")

            if count > 0:
                BuiltIn().log("PDF files:")
                for i, pdf in enumerate(pdf_files, 1):
                    file_size_mb = round(os.path.getsize(pdf) / (1024 * 1024), 2)
                    BuiltIn().log(f"  {i}. {os.path.basename(pdf)} ({file_size_mb} MB)")

            return count

        except Exception as e:
            BuiltIn().log(f"Error checking PDF files: {str(e)}", level='ERROR')
            return 0


# # Example Robot Framework test case
# ROBOT_TEST_EXAMPLE = """
# *** Settings ***
# Library    PDFEmailManager.py
#
# *** Variables ***
# ${SENDER_EMAIL}       your_email@gmail.com
# ${EMAIL_PASSKEY}      your_gmail_app_password
# ${RECEIVER_EMAIL}     recipient@company.com
#
# *** Test Cases ***
# Complete PDF Email Workflow
#     [Documentation]    Process latest PDF: find, email, and delete
#     [Tags]    pdf    email    automation    workflow
#
#     # Optional: Set custom download folder
#     ${folder_result}=    Set PDF Download Folder    downloads
#     Should Be Equal    ${folder_result}    SUCCESS
#
#     # Check if PDFs are available
#     ${pdf_count}=    Check PDF Files Count
#     Should Be True    ${pdf_count} > 0    No PDF files found in download folder
#
#     # Execute the main workflow
#     ${workflow_result}=    Process PDF Email Workflow
#     ...    ${SENDER_EMAIL}    ${RECEIVER_EMAIL}    ${EMAIL_PASSKEY}
#
#     # Verify success
#     Should Be Equal    ${workflow_result}    SUCCESS    PDF workflow failed
#
#     Log    PDF email workflow completed successfully!
#
# Test Download Folder Management
#     [Documentation]    Test download folder configuration
#     [Tags]    configuration
#
#     # Get current folder
#     ${current_folder}=    Get Current Download Folder
#     Log    Current folder: ${current_folder}
#
#     # Change to custom folder
#     ${result1}=    Set PDF Download Folder    test_downloads
#     Should Be Equal    ${result1}    SUCCESS
#
#     # Verify change
#     ${new_folder}=    Get Current Download Folder
#     Should Contain    ${new_folder}    test_downloads
#
#     # Reset to default
#     ${result2}=    Set PDF Download Folder    downloads
#     Should Be Equal    ${result2}    SUCCESS
#
# Handle No PDF Files Scenario
#     [Documentation]    Test behavior when no PDF files are present
#     [Tags]    error_handling
#
#     # Set to empty folder
#     ${result}=    Set PDF Download Folder    empty_folder
#     Should Be Equal    ${result}    SUCCESS
#
#     # Try workflow (should fail gracefully)
#     ${workflow_result}=    Process PDF Email Workflow
#     ...    ${SENDER_EMAIL}    ${RECEIVER_EMAIL}    ${EMAIL_PASSKEY}
#
#     Should Be Equal    ${workflow_result}    FAILURE
#     Log    Workflow correctly failed when no PDF files found
# """
#
# if __name__ == "__main__":
#     # Example usage for testing
#     print("PDF Email Manager - Robot Framework Library")
#     print("=" * 60)
#
#     manager = PDFEmailManager()
#
#     # Test folder operations
#     print("\nTesting folder operations...")
#     result = manager.set_pdf_download_folder("test_downloads")
#     print(f"Set folder result: {result}")
#
#     current_folder = manager.get_current_download_folder()
#     print(f"Current folder: {current_folder}")
#
#     pdf_count = manager.check_pdf_files_count()
#     print(f"PDF count: {pdf_count}")
#
#     print("\nTo test the complete workflow, configure email settings and call:")
#     print("manager.process_pdf_email_workflow('sender@gmail.com', 'receiver@email.com', 'app_password')")
#
#     print("\n" + "=" * 60)
#     print("Robot Framework Usage:")
#     print("Save this file as PDFEmailManager.py")
#     print("Import in .robot files with: Library    PDFEmailManager.py")
#     print("Use keyword: Process PDF Email Workflow")