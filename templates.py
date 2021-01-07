############### TBI Files ##################

# The actual functions in the .c and .h files for TBIs
function_signature_template = "double {}(double3 GA, double3 GB, double3 GC, double Z)"
c_function_template = \
"""{0} {{
    return {1};
}}
"""
h_function_template = "{};\n"


################## Property Integrals ###################


# for the functions with cases that call the integrals
case_template ="""if (II == {} && JJ == {}) {{
{}
}}"""

# Data structure to hold all templates
templates = {
    "signature": function_signature_template,
    "c_function": c_function_template,
    "h_function": h_function_template,
    "case": case_template
}


def apply_template(key, *args):
    key = key.lower()
    if key not in templates.keys():
        raise ValueError("{} not a valid template".format(key))
    return templates[key].format(*args)

# This cute function takes a block of text and creates a visually pleasing C-style
# comment block out of it.
def generate_disclaimer(text):
    N = 80
    buffer_length = 8 # This just looks good
    
    # derived
    chars_per_line = N - 2 - 2*buffer_length
    buffer = " "*buffer_length
    
    # The outputted disclaimer
    s = ""
    s += "/" + "*" * (N-1) + "\n" # first line
    s += "{0}{1}{0}\n".format("*", " "*(N-2)) # Empty line for vertical spacing
    
    text = text.replace('\n', ' ').strip()
    words = text.split()
#     assert all([len(w) <= buffer_length for w in words]) # makes sure no words or URLs are too long for a line
    counter = 0
    iw = 0
    while iw < len(words):
        counter += 1
        length = 0
        line = words[iw]
        if len(line) > chars_per_line:
            print('Warning: "{}" has length {}, which exceeds the allowed line length of {}'.format(line, len(line), chars_per_line))
        iw += 1
        for jw in range(iw, len(words)):
            w = words[jw]
            if len(line) + len(w) + 1 <= chars_per_line:
                line += " " + w
                iw += 1
            else:
                break

        if counter == 20:
            return
        num_extra_spaces = chars_per_line - len(line)
        left_spaces = " " * int(num_extra_spaces/2)
        right_spaces = " " * (int(num_extra_spaces/2) + num_extra_spaces % 2)
        line = "{0}{1}{2}".format(left_spaces, line, right_spaces)
        
        s += "{0}{1}{2}{1}{0}\n".format("*", buffer, line)
    
    s += "{0}{1}{0}\n".format("*", " "*(N-2)) # Empty line for vertical spacing
    s += "*" * (N-1) + "/\n" # last line
    return s