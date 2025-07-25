# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START sheets_quickstart]
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'servicecredentials.json'

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1DJmUp6qd7gZxrlHdUcjwTA1pnDFES7iYq_GfAoyNkHE'
RANGE_NAME = 'Blad1'


def main():
  creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])

    if not values:
      print("No data found.")
      return

    #print('Found data in range: ' + result.get('range', 'Geen'))
    #r = 0
    for r, row in enumerate(values):
      print(str(r+1) + ': ', end='')
      print(row)
      if (row[0] == '59322291'): 
        found_row = r
  except HttpError as err:
    print(err)

  try:
    # Write additional row, just to figure out how to
    writevalues = [
      [
        'X', '29-2-2024', -10
      ]
      # Additional rows ...
    ]

    print('Writing values: ', end='')
    print(writevalues)

    WRITE_RANGE_NAME = 'E' + str(found_row) + ':' + 'G' + str(found_row)
    print('Write to range: ' + WRITE_RANGE_NAME)

    body = {"values": writevalues}
    result = (
      service.spreadsheets()
      .values()
      .update(
          spreadsheetId=SPREADSHEET_ID,
          range=WRITE_RANGE_NAME,
          valueInputOption='USER_ENTERED',
          body=body,
      )
      .execute()
    )
    print(f"{result.get('updatedCells')} cells updated.")
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

if __name__ == "__main__":
  main()
# [END sheets_quickstart]
