# Prompts

SYSTEM_PROMPT = """
You are an AI assistant responsible for generating the necessary actions for a Web Agent to complete a given task successfully.
"""

OUTPUT_REQ_PROMPT = """
# CRITICAL REQUIREMENTS:
- 1. Output only the raw JSON array, without backticks, code blocks, or markdown.
- 2. Do not include any introductory or concluding text.
- 3. Ensure the JSON strictly begins with '[' and ends with ']'.
"""

FIRST_MISSION_PROMPT = """
# Objective
Generate a JSON-formatted list of Action objects for the Web Agent to execute tasks on a web site specified by **Task Prompt**.
The Web Agent sequentially performs these actions using Playwright.
the first Action must start from the URL of main page specified in the **Task Prompt**.

# **Task Prompt**
{task_prompt}.
The url for main page is `{portal_url}`.
Notice that it is not for real-world web page, so you must only use it in output.

# Action Object Structure
Each Action object describes a one-step action to perform the task.
Each Action object consists of:
- `type`: Specifies the action type.
- `selector`: Identifies the target element (null if not applicable).
- Additional fields (vary based on action type).

## Action Types and Their Additional Fields  

### 1. ClickAction  
Performs a click on a specified HTML element. If coordinates (`x`, `y`) are provided, the `selector` field can be null.  

**Additional Fields:**  
- `x` (optional): X-coordinate of the click position.  
- `y` (optional): Y-coordinate of the click position.  

### 2. DoubleClickAction  
Performs a double-click on the specified element.  

**Additional Fields:**  
_None_  

### 3. NavigateAction  
Navigates to a different page or moves forward/backward in browsing history.  

**Additional Fields:**  
- `url`: The target URL (if navigating to a specific page).  
- `go_back`: Boolean, `true` if navigating back in history.  
- `go_forward`: Boolean, `true` if navigating forward in history.  

### 4. TypeAction  
Types text into an input field.  

**Additional Fields:**  
- `text`: The text to be typed into the element.  

### 5. SelectAction  
Selects an option from a dropdown menu or selection field.  

**Additional Fields:**  
- `value`: The option value to be selected.  

### 6. HoverAction  
Moves the cursor over a specified element.  

**Additional Fields:**  
_None_  

### 7. WaitAction  
Pauses execution for a specified duration.  

**Additional Fields:**  
- `time_seconds`: Duration to wait, in seconds.  

### 8. ScrollAction  
Scrolls up or down within a page or element.  

**Additional Fields:**  
- `value`: Distance to scroll or a text value to scroll to.  
- `up`: Boolean, `true` to scroll up.  
- `down`: Boolean, `true` to scroll down.  

### 9. SubmitAction  
Submits a form by pressing Enter or clicking the submit button.  

**Additional Fields:**  
- `selector`: Must explicitly reference the submit button if available. If no button exists, `selector` can be null.  

### 10. DragAndDropAction  
Drags one element and drops it onto another.  

**Additional Fields:**  
- `source_selector`: Selector for the element being dragged.  
- `target_selector`: Selector for the element to drop onto.  

### 11. ScreenshotAction  
Captures a screenshot of the page.  

**Additional Fields:**  
- `file_path`: The file path where the screenshot should be saved.  

### 12. GetDropDownOptions  
Retrieves the available options in a dropdown menu.  

**Additional Fields:**  
_None_  

### 13. SelectDropDownOption  
Selects an option from a dropdown menu based on its visible text.  

**Additional Fields:**  
- `text`: The visible text of the option to select.  

## Selector Field in an Action Object  
Each `Action` object contains a `selector` field, which is a `Selector` object used to identify the target HTML element.
If an action does not require an element, `selector` must be `null`.  

### Selector Object Structure  
A `Selector` object consists of the following fields:  
- `type`: Specifies the selector type. Can be `"attributeValueSelector"`, `"tagContainsSelector"`, or `"xpathSelector"`.  
- `attribute` (only for `"attributeValueSelector"`): Defines the attribute used for selection (`"id"`, `"class"`, or `"name"`).  
- `value`: Specifies the selector value based on the type.  

### Selector Types  

#### 1. attributeValueSelector  
Selects an element based on a specific attribute.  

**Additional Fields:**  
- `attribute`: The attribute used for selection (`"id"`, `"class"`, or `"name"`).  
- `value`: The attribute's value.  

**Rules:**  
- If `attribute` is `"id"`, `value` must be prefixed with `#`.  
- If `attribute` is `"class"`, `value` must be prefixed with `.`.  
- If `attribute` is `"name"`, `value` must match the `name` attribute of the element.  

#### 2. tagContainsSelector  
Selects an element based on its tag name and partial content.  

**Additional Fields:**  
- `value`: The tag name of the HTML element.  

#### 3. xpathSelector  
Selects an element using an XPath expression.  

**Additional Fields:**  
- `value`: The XPath query identifying the element. 

# Provided Information
Following is the url of main page and corresponding uploaded file names.
{portal_url} : {file_uploaded}

# First Misson: Fetching the HTML contents of the pages which are required to navigate
I gave you the url of main page on the web site and upload the file which has its brief HTML contents.
First of all, Analyze the uploaded main page file and check if it is required for the web agent to navigate another pages from the main page in order to perform the task specified in **Task Prompt**.
If it is required, output only URLs that are required for Web agent to navigate directly in order to perform the task; otherwise output [].
URLs must be a JSON-formatted list of full URLs.
"""

NEXT_MISSION_PROMPT = """
# Next Mission: Fetching the HTML contents of the another pages which are required to navigate
I uploaded files which have brief HTML contents of the additional page urls that are required to perform the task specified in **Task Prompt**.
You must analyze it and identify if another pages are required for the Web Agent to navigate in order to perform the task specified in **Task Prompt**.
If it is required, output only URLs that are required for Web agent to navigate directly in order to perform the task; otherwise output [].
URLs must be a JSON-formatted list of full URLs.

## Provided Information
Followings are the urls of pages and corresponding uploaded file names.
{urls_uploaded}
"""


LAST_MISSION_PROMPT = """
# Last Mission: Genernate the list of Action objects
Generate a JSON-formatted list of Action objects to execute tasks on web pages specified by **Task Prompt**.
"""