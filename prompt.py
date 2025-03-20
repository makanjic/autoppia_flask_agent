# Prompts

CONVERT_RESPONSE_TO_JSON_PROMPT = """
You are an AI assistant designed to generate actions required for a Web Agent to perform a given task successfully.

## CRITICAL REQUIREMENTS:
1. Return ONLY the raw JSON array without any backticks, code blocks, or markdown
2. Do not include any text before or after the JSON array
3. The JSON must start with '[' and end with ']'
"""


REQUEST_ACTIONS_PROMPT = """
## Objective
You will receive a **Task Prompt** and must generate a json-formatted list of Action objects required to perform it in a web page.
Then the Web Agent performs one-step actions which are described sequentially in the list of Action objects, by means of playwright.
The first Action object must represent the one-step action to navigate to the url specified in the task prompt.



## Composition of a Action object
Each Action object describes a one-step action to perform the task.
Each Action object must contain "type" and "selector" fields.

### "type" field in a Action object
The "type" field of a Action object is a string that contains one of "ClickAction", "DoubleClickAction", "NavigateAction", "TypeAction", "SelectAction", "HoverAction", "WaitAction", "ScrollAction", "SubmitAction", "DragAndDropAction", "ScreenshotAction", "GetDropDownOptions", "SelectDropDownOption" strings.

#### In the case of "type" field contains "ClickAction"
If the "type" field in a Action object contains "ClickAction", it means that the one-step action is to click a HTML element specified by "selector" field in the Action object.
In this case, the Action object has optional "x", "y" fields.
The "x", "y" fields specified the location in which the click action occurs.
The "x" field is the x coordinated position by pixel from the left of the web page.
The "y" field is the y coordinated position by pixel from the top of the web page.
if the "x", "y" fields contains valid numerical values, then the "selector" field may have null value.
If the "selector" field has a valid value, then the "x", "y" fields can contain null value.

#### In the case of "type" field contains "DoubleClickAction"
If the "type" field in a Action object contains "DoubleClickAction", it means that the one-step action is to double click a HTML element specified by "selector" field in the Action object.

#### In the case of "type" field contains "NavigateAction"
If the "type" field in a Action object contains "NavigateAction", it means that the one-step action is to navigate a different web page.
In this case, the Action object has "url", "go_back", "go_forward" fields.
And the "selector" field in a Action object has null value.
The "go_back", "go_forward" fields have boolean values.
If the "go_back" field has True value, it means the one-step action is to go backward in the browsing history.
If the "go_forward" field has True value, it means the one-step action is to go forward in the browsing history.
If neither both fields are True, it means the one-step action is to go to page specified by the "url" field.

#### In the case of "type" field contains "TypeAction"
If the "type" field in a Action object contains "TypeAction", it means that the one-step action is to type a text into the HTML element specified by "selector" field in the Action object.
In this case, the Action object has additional "text" field.
The "text" field has the value to type into the HTML element.

#### In the case of "type" field contains "SelectAction"
If the "type" field in a Action object contains "SelectAction", it means that the one-step action is to select a option among the options listed in the HTML element specified by "selector" field in the Action object.
In this case, the Action object has additional "value" field.
The "value" field contains the option value to be selected.

#### In the case of "type" field contains "HoverAction"
If the "type" field in a Action object contains "HoverAction", it means that the one-step action is to hover the cursor on the HTML element specified by "selector" field in the Action object.

#### In the case of "type" field contains "WaitAction"
If the "type" field in a Action object contains "WaitAction", it means that the one-step action is to wait some seconds.
In this case, the Action object has additional "time_seconds" field.
The "time_seconds" field contains the time to wait in seconds.

#### In the case of "type" field contains "ScrollAction"
If the "type" field in a Action object contains "ScrollAction", it means that the one-step action is to scroll the browser window.
In this case, the Action object has additional "value", "up", "down" fields.
The "up", "down" fields have boolean values.
If the "up" field has True value, it means the one-step action is to scroll upward.
If the "down" field has True value, it means the one-step action is to scroll downward.
The "value" field has the value which represents how long scroll.
The "value" field can have a text value, in this case, it means that the one-step action is to scroll to a HTML element which contains the text.

#### In the case of "type" field contains "SubmitAction"
If the "type" field in a Action object contains "SubmitAction", it means that the one-step action is to press Enter key or click the submit element specified by "selector" field in the Action object in order to submit form data.
In this case, the "selector" field in a Action object must reference explicitly to the button in the submit form.
So the "selector" field can reference the submit button by using attributes such as id and name, or by using xpath selector.
If there is not submit button in the form, the "selector" field can be null value.

#### In the case of "type" field contains "DragAndDropAction"
If the "type" field in a Action object contains "DragAndDropAction", it means that the one-step action is a drag and drop action.
In this case, the Action object has additional "source_selector" and "target_selector" fields.
The "source_selector" and "target_selector" field is strings which are using to refer HTML elements.
The "source_selector" field refers the source HTML element which is dragged.
The "target_selector" field refers the destination HTML element which is dropped onto.

#### In the case of "type" field contains "ScreenshotAction"
If the "type" field in a Action object contains "ScreenshotAction", it means that the one-step action is to make a screenshot for the web browser.
In this case, the Action object has "file_path" field which has pathname to a file.
The "file_path" field refers the file which screenshot saved.

#### In the case of "type" field contains "GetDropDownOptions"
If the "type" field in a Action object contains "GetDropDownOptions", it means that the one-step action is to click a HTML element specified by "selector" field in the Action object, in order to list options in the drop-down menu styled HTML element.

#### In the case of "type" field contains "SelectDropDownOption"
If the "type" field in a Action object contains "SelectDropDownOption", it means that the one-step action is to select a option in the drop-down menu styled HTML element specified by "selector" field in the Action object.
In this case, the Action object has "text" field.
The "text" field contains the value of option to be selected.


### "selector" field in a Action object
The "selector" field of a Action object is a Selector object to specify the element required to perform the one-step action.
If it is not required to specify the element, it must be null.
Otherwise, the Selector object has "type" and "attribute", "value" fields.
The "type" field of a Selector object contains one of "attributeValueSelector", "tagContainsSelector", "xpathSelector" strings.

#### In the case of "type" field in a Selector object contains "attributeValueSelector"
If the "type" field of a Selector object has "attributeValueSelector" string, the "attribute" field of a Selector object must have one of "id", "class", "name" strings.

##### In the case of "attribute" field in a Selector object contains "id"
If the "attribute" field of a Selector object has "id" string, the "value" field of a Selector object contains the id of the HTML element required to perform the one-step action.
In this case, the "value" field must contain the "#" prefix and the the id attribute of the HTML element.

##### In the case of "attribute" field in a Selector object contains "class"
If the "attribute" field of a Selector object has "id" string, the "value" field of a Selector object contains the class of the HTML element required to perform the one-step action.
In this case, the "value" field must contain the "." prefix and the class attribute of the HTML element.

##### In the case of "attribute" field in a Selector object contains "name"
If the "attribute" field of a Selector object has "name" string, the "value" field of a Selector object contains the name of the HTML element required to perform the one-step action.
In this case, the "value" field must contain the name attribute of the HTML element.

#### In the case of "type" field in a Selector object contains "tagContainsSelector"
If the "type" field of a Selector object has "tagContainsSelector" string, the "value" field of a Selector object contains tag name of the HTML element required to perform the one-step action.

#### In the case of "type" field in a Selector object contains "xpathSelector"
If the "type" field of a Selector object has "xpathSelector" string, the "value" field of Selector object contains XPath reference to the HTML element required to perform the one-step action.



## **Task Prompt**
{task_prompt}



## Brief HTML for the web pages
The brief HTML for the web pages are on uploaded files.
Followings are page urls and corresponding uploaded file names.
{urls_uploaded}
"""



USER_FETCH_URL_PROMPT = """
## Objective
You will receive a **Task Prompt** and must gather HTML contents of page urls required to perform the task.


## **Task Prompt**
{task_prompt}


## Brief HTML for the web page
The brief HTML for the web page is on uploaded files.
Followings are page urls and corresponding uploaded file names.
{urls_uploaded}

Output the page urls in json-formatted list, if there is need to know HTML contents of additional page urls, in order to perform the **Task Prompt**. 
If there is no need to know additional urls, output empty json-formatted list [].
the page urls must be full url.


## CRITICAL REQUIREMENTS:
1. Return ONLY the raw JSON array without any backticks, code blocks, or markdown
2. Do not include any text before or after the JSON array
3. The JSON must start with '[' and end with ']'
"""