'''
This module takes in a json file of a diagram and its script, and
returns a parse matrix. This matrix is used in generating reveal.js 
slides. 

The parse matrix is a pandas DataFrame, where each row is a frame
and each column is an object. The value of the cell is 1 if the
object appears in the frame, and 0 otherwise.

Call function get_matrix(data, script) to get the parse matrix. Every 
other function is only a helper to this function. 
'''
import sys 
import json 
import pandas as pd

def preprocess_script(script):
    '''
    This function preprocesses the script, replacing all "&lt;" 
    and "&gt;" with "<" and ">", respectively. 

    Input
    -----
        script: str
            The script of the diagram.
    Return
    ------
        script: str 
            The preprocessed script of the diagram, with all 
            "&lt;" and "&gt;" replaced.
    '''
    script = script.replace("&lt;", "<")
    script = script.replace("&gt;", ">")
    return script

def get_script_map(script):
    '''
    This function returns a dictionary mapping object_id to
    the frame number slice that it should appear in. 

    Input
    -----
        script: str
            The script of the diagram.
    Return
    ------
        script_map: dict
            A dictionary mapping object_id to the frame number slice.
    '''
    script_map = {}
    script_line = script.split("\n")
    for line in script_line: 
        for i in range(len(line)): 
            if line[i] == "<":
                start = i+1
            if line[i] == ">":
                stop = i
                object_id = line[stop+1:].strip()
                object_sequence_slice = line[start:stop]
                script_map[object_id] = object_sequence_slice
    return script_map

def get_text_script_map(script_map, textbox_list):
    '''
    This function selects script_map items that are of type textbox. 
    All other types of objects (images, katex, etc.) are ignored. 

    Input
    -----
        script_map: dict
            A dictionary mapping object_id to the frame number slice.
        textbox_list: list
            A list of all textbox id.
    Return
    ------
        text_script_map: dict
            A dictionary mapping textbox_id to the frame number slice.
    '''
    text_script_map = {}
    keylist = list(script_map.keys())
    for i in range(len(keylist)): 
        for id in textbox_list: 
            if keylist[i].startswith(id): 
                text_script_map.update({keylist[i] : script_map[keylist[i]]})
    return text_script_map

def get_enumerated_text_script_map(text_script_map, textbox_shape): 
    '''
    text_script_map may have items that are the slice of a textbox. 
    For example, "<1> tbox[1:3]" means that tbox[1], tbox[2], and tbox[3]
    are all visible in frame 1. 
    
    This function enumerates the slice of a textbox into individual
    textbox cells. 

    Input
    -----
        text_script_map: dict
            A dictionary mapping textbox_id to the frame number slice.
        textbox_shape: dict
            A dictionary mapping textbox_id to its shape (number of rows).
    Return
    ------
        enum_text_script_map: dict
            A dictionary mapping textbox_id to the frame number slice,
            where the frame number slice is enumerated into individual  
            textbox cells.
    '''
    enum_text_script_map = {}
    for obj_id, obj_seq in text_script_map.items():
        start_tbox_cell = 0 
        stop_tbox_cell = 0 
        new_obj_id = ""

        # case 1: whole box, no slicing 
        if "[" not in obj_id: 
            start_tbox_cell = 1; 
            stop_tbox_cell = textbox_shape[obj_id]
            new_obj_id = obj_id

            for i in range(start_tbox_cell, stop_tbox_cell+1):
                enum_text_script_map[new_obj_id + "[" + str(i) + "]"] = obj_seq
        # case 2: slicing 
        elif ":" in obj_id: 
            start_left_index = 0 
            end_left_index = 0 
            start_right_index = 0 
            end_right_index = 0 
            for i in range(len(obj_id)): 
                if obj_id[i] == "[": 
                    start_left_index = i+1 
                elif obj_id[i] == ":": 
                    end_left_index = i 
                    start_right_index = i+1 
                elif obj_id[i] == "]": 
                    end_right_index = i 
            
            str_start_tbox_cell = obj_id[start_left_index : end_left_index]
            str_stop_tbox_cell = obj_id[start_right_index : end_right_index]
            new_obj_id = obj_id[:start_left_index-1]
            start_tbox_cell = 0 if str_start_tbox_cell == "" else int(str_start_tbox_cell)
            stop_tbox_cell = textbox_shape[new_obj_id] if str_stop_tbox_cell == "" else int(str_stop_tbox_cell)
            
            for i in range(start_tbox_cell, stop_tbox_cell+1): 
                enum_text_script_map[new_obj_id + "[" + str(i) + "]"] = obj_seq
        
        # case 3: one cell of textbox already identified, append as is 
        else: 
            enum_text_script_map[obj_id] = obj_seq

    return enum_text_script_map

def get_split_text_map(data): 
    '''
    This function returns a dictionary mapping textbox_id to its
    content, split by line.

    Input
    -----
        data: dict (json)
            The json file of the diagram.
    Return
    ------
        split_text_map: dict
            A dictionary mapping textbox_id to its content, split by line.
    '''
    split_text_map = {} # text_id: [text_line]
    for i in range(len(data["text"])):
        this_text_box_id = data["text"][i]["id"]
        this_text_box = data["text"][i]["content"].split("\n")
        split_text_map[this_text_box_id] = this_text_box
    return split_text_map

def get_textbox_shape(split_text_map):
    '''
    This function returns a dictionary mapping textbox_id to its
    shape (number of rows).

    Input
    -----
        split_text_map: dict
            A dictionary mapping textbox_id to its content, split by line.
    Return
    ------
        textbox_shape: dict 
            A dictionary mapping textbox_id to its shape (number of rows).
    '''
    textbox_shape = {} # text_id: n_line
    textbox_list = list(split_text_map.keys())
    for i in range(len(textbox_list)): 
        textbox_shape[textbox_list[i]] = len(split_text_map[textbox_list[i]])
    return textbox_shape


def strip_sugarcoat(data, script): 
    '''
    A script line that reads "<1> tbox[1:3]" means that tbox[1], tbox[2],
    and tbox[3] are all visible in frame 1. This is the syntax sugar of 
    this scripting language (called "sugarcoating"). 

    This function strips the sugarcoat and returns an explicitly enumerated 
    script. Every table slice is enumerated into individual cells.

    Input
    -----
        data: dict (json)
            The json file of the diagram.
        script: str
            The script of the diagram.
    Return
    ------
        new_script: str 
            The explicitly enumerated script of the diagram.
    '''
    script_lines = script.split("\n")
    new_script_lines = [] 

    # find all items that is NOT a textbox and add it to new_script_lines
    # add more (table, shape) when these objects are available 
    not_textbox_list = [] 
    for i in range(len(data["image"])):
        not_textbox_list.append(data["image"][i]["id"])
    for i in range(len(data["katex"])):
        not_textbox_list.append(data["katex"][i]["id"])
    
    for line in script_lines:
        for id in not_textbox_list: 
            if id in line: 
                new_script_lines.append(line)
    
    # now de-sugarcoat textbox script lines
    script_map = get_script_map(script)
    split_text_map = get_split_text_map(data)
    textbox_shape = get_textbox_shape(split_text_map)
    textbox_id_list = list(textbox_shape.keys())
    text_script_map = get_text_script_map(script_map, textbox_id_list)
    enum_script_map = get_enumerated_text_script_map(text_script_map, textbox_shape)

    for obj_id, obj_seq in enum_script_map.items():
        new_script_line = "<" + obj_seq + "> " + obj_id
        new_script_lines.append(new_script_line)
    
    new_script = "\n".join(new_script_lines)
    return new_script


def get_number_of_unit_items(data, split_text_map): 
    ''' 
    [UNUSED] 
    This function returns the number of unit-sized items in the diagram.
    Unit-sized items are objects that cannot be divided into smaller 
    units. For example, a table is not an unit-sized item, but individual 
    table cells are unit-sized items.

    This function ended up not being used at all :) 

    Input
    -----
        data: dict (json)
            The json file of the diagram.
        split_text_map: dict
            A dictionary mapping textbox_id to its content, split by line.
    Return
    ------
        n_unit_sized_items: int
            The number of unit-sized items in the diagram.
    '''
    n_text_line = 0
    for item in split_text_map.values(): 
        n_text_line += len(item)

    n_unit_sized_items = len(data["image"]) + len(data["katex"]) + n_text_line 
    return n_unit_sized_items


def get_number_of_frames(script_map):
    '''
    This function returns the maximum number of frames in the diagram.
    These will determine the number of rows in the final parse matrix. 

    Input
    -----
        script_map: dict
            A dictionary mapping object_id to the frame number slice.
    Return
    ------
        n_frame: int
            The maximum number of frames in the diagram.
    '''
    sequence_slice = list(script_map.values())
    sequence_num = [] 
    for i in range(len(sequence_slice)): 
        if sequence_slice[i].find("-") == -1: 
            sequence_num.append(int(sequence_slice[i]))
        elif sequence_slice[i][-1] == "-": 
            sequence_num.append(int(sequence_slice[i][:-1])) 
        else: 
            tmp = sequence_slice[i].split("-")
            tmp = [int(k) for k in tmp]
            sequence_num.extend(tmp)

    n_frame = max(sequence_num)
    return n_frame

def get_object_index_map(script, n_frame):
    '''
    This function returns a dictionary mapping object_id to a list of 
    frame numbers that this object appears in.

    Input
    -----
        script: str
            The script of the diagram.
        n_frame: int
            The maximum number of frames in the diagram.
    Return
    ------
        object_index_map: dict
            A dictionary mapping object_id to a list of frame numbers.
    '''
    script_line = script.split("\n")
    object_index_map = {} # object_id: [object_index]

    for line in script_line: 
        for i in range(len(line)): 
            if line[i] == "<":
                start = i+1
            if line[i] == ">":
                stop = i
                object_id = line[stop+1:].strip()
                object_index_slice = line[start:stop]
                object_index = []
                if object_index_slice.find("-") == -1: 
                    object_index.append(int(object_index_slice))
                elif object_index_slice[-1] == "-": 
                    all_visible_frames = list(range(int(object_index_slice[:-1]), n_frame + 1))
                    object_index.extend(all_visible_frames)
                else: 
                    tmp = object_index_slice.split("-")
                    tmp = [int(k) for k in range(int(tmp[0]), int(tmp[1])+1)]
                    object_index.extend(tmp)
                object_index_map[object_id] = object_index

    return object_index_map

def get_parse_matrix(object_index_map, n_frame):
    '''
    This function creates a parse matrix, where each row is a frame
    and each column is an object. The value of the cell is 1 if the
    object appears in the frame, and 0 otherwise.

    Input
    -----
        object_index_map: dict
            A dictionary mapping object_id to a list of frame numbers.
        n_frame: int
            The maximum number of frames in the diagram.
    Return
    ------
        mat: pandas.DataFrame
            The parse matrix of the diagram.
    '''
    col_label = object_index_map.keys()
    row_label = list(range(n_frame + 1))
    mat = pd.DataFrame(0, index=row_label, columns=col_label)

    for key, value in object_index_map.items(): 
        for i in value: 
            mat.loc[i, key] = 1
    
    return mat

def get_matrix(data, script):
    '''
    [MAIN FUNCTION]
    This is a wrapper function that calls all the functions above to
    return the parse matrix of the diagram.

    Input
    -----
        data: dict (json)
            The json file of the diagram.
        script: str
            The script of the diagram.
    Return
    ------
        mat: pandas.DataFrame
            The parse matrix of the diagram.
    '''
    script_map = get_script_map(script)
    n_frame = get_number_of_frames(script_map)
    stripped_script = strip_sugarcoat(data, script)
    script_frame_map = get_object_index_map(stripped_script, n_frame)

    mat = get_parse_matrix(script_frame_map, n_frame)

    return mat

#------------- READ INPUT FILE -------------
# i don't know how to do the sys.argv thing so i put the input json 
# file in the same directory as this script and name it input.json :) 
with open('input.json') as f:
    data = json.load(f)

script = data["diagram"][0]["script"] 
script = preprocess_script(script)

print(get_matrix(data, script))