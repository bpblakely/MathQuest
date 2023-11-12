import PyPDF2
import re

import requests
import json
from pdf2image import convert_from_path
import io
import pandas as pd

# Your Mathpix credentials
APP_ID = "personal_92425e_22ce21"
APP_KEY = "7269c14b69f17b785cc041a6209007bb626249893f755031f7db8576c6113694"
HEADERS = {
    "app_id": APP_ID,
    "app_key": APP_KEY
}

# Convert page range to images and process each with Mathpix OCR
def extract_pages_and_process(pdf_path, start_page, end_page):
    # Don't need to define poppler_path if it's already in PATH
    pages =  convert_from_path(pdf_path, dpi=300, first_page=start_page, last_page=end_page) # poppler_path=r'C:\Program Files\poppler-23.10.0\Library\bin'
    
    all_text = ""
    for i, page in enumerate(pages):
        # Convert image to in-memory binary stream
        buffer = io.BytesIO()
        page.save(buffer, format="JPEG")
        buffer.seek(0)
        
        # Send the image to Mathpix OCR API
        r = requests.post("https://api.mathpix.com/v3/text",
                          files={"file": buffer},
                          data={
                              "options_json": json.dumps({
                                  "math_inline_delimiters": ["$", "$"],
                                  "rm_spaces": True,
                                  "formats":'text',
                                  'numbers_default_to_math':True
                                  # "data_options":{
                                  #      #'include_svg':True,
                                  #     #'include_mathml':True,
                                  #     #'include_latex':True,
                                  #     'include_asciimath':True
                                  #     }
                              })
                          },
                          headers=HEADERS)
        data = r.json()
        all_text += data['text'] +"\n"
    return all_text
#%%

def extract_outline(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_content = file.read()
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    outlines = reader.outline
    return list(extract_items_from_outlines(outlines, reader))

def extract_items_from_outlines(outlines, reader):
    for item in outlines:
        if isinstance(item, list):
            # Recursive call for nested items
            yield from extract_items_from_outlines(item, reader)
        else:
            yield item, reader
def get_page_number(reader, page_obj):
    for i, page in enumerate(reader.pages):
        if page == page_obj:
            return i + 1  # '+ 1' to get 1-based page numbering
    return None  # return None if page not found


def get_questions(data_text):
    questions = []
    current_question = []
    
    for line in data_text.split('\n'):
        if re.match(r"^\$\d+\$", line):  # Check if the line starts with a pattern like "$1$"
            if current_question:  # If there's a current question, append it to the questions list
                questions.append("\n".join(current_question))
                current_question = []  # Reset the current question
        current_question.append(line)
    
    # Add the last question if there's any
    if current_question:
        questions.append(" ".join(current_question))
        
    # start_index = 0
    # for i in range(len(questions)):
    #     if re.match(".*EXERCISES\s+\d+\.[A-Z]",questions[i]):
    #         exercise_section = re.findall("EXERCISES\s+(\d+\.[A-Z])", questions[i])[0]
    #         start_index = i+1
    #     #questions[i] = questions[i].replace('\n'," ")
    #     re.findall(r"^\$\d+\$", questions[i])
    return questions

def to_frame(data,start_page):
    exercise_section = None
    start_index = 0
    for index,line in enumerate(data):
        match = re.search(r"EXERCISES\s+(\d+\.[A-Z])", line)
        if match:
            exercise_section = match.group(1)
            start_index = index+1
    if exercise_section is None:
        for index,line in enumerate(data):
            match = re.search(r"EXERCISES\s+(\$?\d+(\.\w)?\$?)", line)
            if match:
                exercise_section = match.group(1).replace('$', '') 
                start_index = index+1
    if not exercise_section:
        raise ValueError("Exercise section not found in data!")

    # Extracting questions
    questions = []
    question_number = None


    for idx, line in enumerate(data[start_index:]):
        
        match = re.match(r"^\$(\d+)\$", line)  # Check if the line starts with a pattern like "$1$"
        if match:

            question_number = match.group(1)
            questions.append({
                "page": start_page,
                "section": exercise_section,
                "qnumb": question_number,
                "question": line[len(str(question_number))+2:].strip().replace('\n'," ") # Question is empty as it's only 1 line long
            })

    df = pd.DataFrame(questions)
    return df
#%%
pdf_path = r'G:\2015_Book_LinearAlgebraDoneRight.pdf'
outlines = list(extract_outline(pdf_path))
page_list = []
for index, (item, reader) in enumerate(outlines):
    if re.search(r'EXERCISES', item.title, re.IGNORECASE):
        
        # Check if next section is also EXERCISES
        if (index + 1 < len(outlines) and 
            re.search(r'EXERCISES', outlines[index + 1][0].title, re.IGNORECASE)):
            continue  # Skip the current, move to the next
        
        start_page_obj = item.page.get_object()
        start_page_num = get_page_number(reader, start_page_obj)
        
        # Try to determine the end page based on the next outline item
        if index + 1 < len(outlines):
            next_item, _ = outlines[index + 1]
            end_page_obj = next_item.page.get_object()
            end_page_num = get_page_number(reader, end_page_obj) - 1  
                
        else:
            end_page_num = len(reader.pages)  # Last page if it's the last outline item
        
        # Extract text from the range
        print(start_page_num,end_page_num)
        page_list.append([start_page_num,end_page_num])
#FYI: I manually removed stuff in this list to make it match
#%%


# Your Mathpix credentials
APP_ID = "personal_92425e_22ce21"
APP_KEY = "7269c14b69f17b785cc041a6209007bb626249893f755031f7db8576c6113694"
HEADERS = {
    "app_id": APP_ID,
    "app_key": APP_KEY
}

pdf_path = r'books/2015_Book_LinearAlgebraDoneRight.pdf'
outlines = list(extract_outline(pdf_path))
li = []

for i in range(len(page_list)):
        start_page = page_list[i][0]
        end_page = page_list[i][1]
        print(start_page,end_page)
        data_result = extract_pages_and_process(pdf_path, start_page, end_page)

        data_text = data_result
        questions = get_questions(data_text)
        temp_df = to_frame(questions,start_page)
        li.append(temp_df)
        
      

#%%
df = pd.concat(li)
df['isbn'] = "978-3-319-11079-0" # this is what we are going to use to tie books together
df.to_csv(r'temp_questions.csv',index=False)
#%%

# Lets try a calculus textbook that has graphs and stuff in the problem statement

pdf_path = r'books/calculus-10th-edition-anton.pdf'
outlines = list(extract_outline(pdf_path))

#%%
start_section = ".*0.2: New Functions from Old.*"
end_pattern = r"EXERCISE SET \d+\.\d+"
end_pattern_space =  r"EXERCISE SET \d+\ .\d+"
end_pattern_chapter = r"CHAPTER \d+\ REVIEW EXERCISES"

# Store questions
questions = []

# Flag to start extraction
start_extraction = False

with open(pdf_path, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    for i,page in enumerate(reader.pages):
        
        text = page.extract_text()
        if i == 33:break
        if start_extraction:
            # Check for ending section
            if re.search(end_pattern, text):
                break
            # Extract questions from this page
            # (You might need some pattern or logic to correctly split or identify individual questions)
            questions.append(text) 
        elif start_section in text:
            re.search(start_section,text)
            start_extraction = True

# Now, `questions` will contain the questions extracted from the section.
print(questions)

#%%

page_list = []
outlines = list(extract_outline(pdf_path))
outlines = outlines[12:-7]
last_start_page = 0
with open(pdf_path, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    for index, (item, reader) in enumerate(outlines):
        start_page_obj = item.page.get_object()
        start_page_num = get_page_number(reader, start_page_obj)
        
        # Try to determine the end page based on the next outline item
        if index + 1 < len(outlines):
            next_item, _ = outlines[index + 1]
            end_page_obj = next_item.page.get_object()
            end_page_num = get_page_number(reader, end_page_obj) - 1  
        if end_page_num < start_page_num:
            print('start > end')
            end_page_num = start_page_num
        print(item.title,start_page_num,end_page_num)
        # work backwards from end_page
        current_page = end_page_num
        exercise=None
        while True: 
            text = reader.pages[current_page].extract_text()
            if re.search(end_pattern, text):
                exercise = re.search(end_pattern,text).group(0)
                exercise = exercise.replace('EXERCISE SET ','').strip()
                break
            elif re.search(end_pattern_chapter, text):
                exercise = re.search(end_pattern_chapter,text).group(0)
                exercise = exercise.replace('REVIEW EXERCISES ','').strip()
                exercise = exercise.replace('CHAPTER','').strip()
                break
            elif re.search(end_pattern_space, text):
                exercise = re.search(end_pattern_space,text).group(0)
                exercise = exercise.replace('EXERCISE SET ','').strip()
                exercise = exercise.replace(' ','')
                break
            current_page-=1
        if not current_page == last_start_page:
            page_list.append([current_page,end_page_num,exercise])
        else:
            print('skipping page',current_page)
        last_start_page = current_page
#%%

def get_questions_calc(data_text):
    questions = []
    current_question = []
    pattern = r'(\b\d+)-(\d+)\b'
    

    for line in data_text.split('\n'):
        if re.match(r"\b\d+\.\s", line):  # Check if the line starts with a pattern like "$1$"
            if current_question:  # If there's a current question, append it to the questions list
                questions.append("\n".join(current_question))
                current_question = []  # Reset the current question
        if re.match(pattern, line):
            if current_question:
                questions.append("\n".join(current_question))
                current_question = []  # Reset the current question
        current_question.append(line)
    
    # Add the last question if there's any
    if current_question:
        questions.append(" ".join(current_question))
  
    return questions

def process_data(data):
    descriptor = None  # Holds the extra descriptor for a range of questions
    output = []

    for item in data:
        range_match = re.match(r'(\d+)-(\d+) (.+)', item)
        question_match = re.match(r'(\d+)\. (.+)', item)

        if range_match:
            start, end, descriptor_text = range_match.groups()
            descriptor = (int(start), int(end), descriptor_text)
        elif question_match and descriptor:
            q_num, q_text = question_match.groups()
            q_num = int(q_num)

            if descriptor[0] <= q_num <= descriptor[1]:
                full_question = f"{q_num}. {descriptor[2]} {q_text}"
                output.append(full_question)
            else:
                # If the question number is not in the range of the descriptor, we reset the descriptor
                output.append(item)
                if q_num > descriptor[1]:
                    descriptor = None
        else:
            output.append(item)

    return output
q = get_questions_calc(data_text)
a = process_data(q)

li = []

for i in range(len(page_list)):
        start_page = page_list[i][0]
        end_page = page_list[i][1]
        exercise = page_list[i][2]
        print(start_page,end_page)
        data_text = extract_pages_and_process(pdf_path, start_page, end_page)
        
        questions = get_questions_calc(data_text)
        processed_data = process_data(questions)
        temp_df = to_frame(processed_data,start_page)
        li.append(temp_df)
        