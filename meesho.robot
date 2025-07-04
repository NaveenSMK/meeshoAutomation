*** Settings ***
Library     SeleniumLibrary
Library     String
Library     CSVLibrary
Library     Collections
Library     DateTime
Library     emailManager.py
Variables   meesho_locator.yaml

Test Teardown   Close All Browsers

*** Variables ***
${BROWSER}  chrome
${REMOTE_URL}    None
${url}      https://supplier.meesho.com/panel/v3/new/root/login
${CSV_FILE_PATH}        ${CURDIR}\\credentials.csv
${DOWNLOAD_DIR}         ${CURDIR}\\labeldownload
${SENDER_EMAIL}         navenmohankumar99@gmail.com
${EMAIL_PASSKEY}        vzshebjcyoirkbxh
${VAR_CHROME_OPTIONS}       add_argument("--disable-popup-blocking");add_argument("--window-size=1920,1080");add_argument("--ignore-certificate-errors");add_argument("--ignore-ssl-errors");add_argument("--no-sandbox");add_argument("--disable-setuid-sandbox");add_argument("--disable-dev-shm-usage");add_argument("--disable-gpu");add_argument("--disable-extensions");add_argument("--disable-background-timer-throttling");add_argument("--disable-backgrounding-occluded-windows");add_argument("--disable-renderer-backgrounding");add_argument("--disable-features=TranslateUI");add_argument("--disable-ipc-flooding-protection");add_argument("--disable-web-security");add_argument("--disable-features=VizDisplayCompositor");add_argument("--remote-debugging-port=9222")
#;add_argument("--incognito")
#5971e126e310bc21104ee2c4b435e225-51afd2db-4e6de1a9
#9514545414,onaM@6266,manobca65@gmail.com
#utechtraders@gmail.com,Onam@6266,manobca65@gmail.com

*** Test Cases ***
Meesho download Labels
    [Tags]  meesho
    Set PDF Download Folder    labeldownload
    ${credentials_list}=    read_csv_file_to_associative    ${CSV_FILE_PATH}
    Log To Console    ${DOWNLOAD_DIR}
    ${chrome_options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
    ${prefs}=    Create Dictionary    download.default_directory=${DOWNLOAD_DIR}    download.prompt_for_download=False    download.directory_upgrade=True
    Call Method    ${chrome_options}    add_experimental_option    prefs    ${prefs}
    FOR    ${user}    IN    @{credentials_list}
          TRY
            Run Keyword If    '${REMOTE_URL}' != 'None'
        ...    open browser    ${url}   ${BROWSER}   options=${chrome_options}    remote_url=${REMOTE_URL}
        ...    ELSE
        ...    open browser    ${url}   ${BROWSER}   options=${chrome_options}
#            open browser    ${url}   ${BROWSER}   options=${CHROME_OPTIONS}
            maximize browser window
            set selenium implicit wait    30
            Wait Until Element Is Visible    ${txt_username}   60
            Input Text    ${txt_username}    ${user.userName}
            Input Text    ${txt_password}    ${user.password}
            Click Element    ${btn_login}
            Sleep    1s
            Wait For Condition	return document.readyState == "complete"
            Wait Until Element Is Visible    ${btn_orders}   60
            Click Element    ${btn_orders}
            Wait Until Element Is Visible    ${btn_readyToShip}   60
            Click Element    ${btn_readyToShip}
            Reload Page
            Sleep    2s
            Wait For Condition	return document.readyState == "complete"
            Run Keyword And Continue On Failure    Click Element    ${btn_gotit}
            Wait Until Element Is Visible    ${btn_labelDownloaded}   60
            Click Element    ${btn_labelDownloaded}
            Wait Until Element Is Visible    ${btn_no}   60
            Click Element    ${btn_no}
            sleep   1s
            Wait Until Element Is Visible    ${ele_NoSelected}      30
            sleep   1s
            Wait Until Element Is Visible    ${chk_selectAllRows}   60
            Click Element    ${chk_selectAllRows}
            Wait Until Element Is Visible    ${btn_downloadLabel}   60
            Click Element    ${btn_downloadLabel}
            Sleep    5s
            Wait Until Element Is Visible    ${ele_popup}           60
            Wait Until Element Is Visible    ${btn_downloadLabel}   60
            sleep   2s
            Click Element    ${btn_downloadLabel}
            sleep   50s
            Close All Browsers
            ${status}       Process PDF Email Workflow      ${SENDER_EMAIL}    ${user.receiver_email}    ${EMAIL_PASSKEY}
            Should Be Equal    ${status}    SUCCESS    PDF workflow failed
          EXCEPT    AS  ${error}
            Close All Browsers
            Log    Error: Failed for user - ${user.userName}
            Log To Console    Error occurred: ${error}
            Run Keyword And Continue On Failure    Fail  Test case failed due to caught exception
          END
        END

