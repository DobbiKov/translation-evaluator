import os
import re
import json
import pypandoc 
from bs4 import BeautifulSoup 
from pdfminer.high_level import extract_text 

def get_document_paths(base_dir, lang_code, doc_format):
    """Generates paths for all documents of a specific format and language."""
    ext_map = {'latex': '.tex', 'markdown': '.md', 'myst': '.myst'}
    extension = ext_map.get(doc_format)
    if not extension:
        print(f"Warning: Unknown document format extension for {doc_format}")
        return []

    # For source, just look for original files. For translated, expect lang_code in name.
    if base_dir == config.SOURCE_DIR:
        pattern = re.compile(rf".*{re.escape(extension)}$")
    else:
        # Example: doc_en.tex or doc_de.md
        pattern = re.compile(rf".*{re.escape(lang_code)}{re.escape(extension)}$")

    doc_files = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if pattern.match(f):
                doc_files.append(os.path.join(root, f))
    return doc_files

def extract_natural_language_text(filepath, doc_format):
    """
    Extracts natural language text from a structured document.
    This is a simplification; a full solution would ignore code blocks, math, etc.
    Pandoc is good for this, but could also be done with regex for specific formats.
    """
    if doc_format == 'latex':
        try:
            text = pypandoc.convert_file(filepath, 'plain', format='latex')
            text = re.sub(r'\\cite\{[^}]+\}', '', text) # Remove citations
            text = re.sub(r'\\[a-zA-Z]+', '', text)    # Remove other commands
            return text
        except Exception as e:
            print(f"Error converting LaTeX to plain text with pandoc: {e}")
            return ""
    elif doc_format in ['markdown', 'myst']:
        try:
            text = pypandoc.convert_file(filepath, 'plain', format=doc_format)
            return text
        except Exception as e:
            print(f"Error converting {doc_format} to plain text with pandoc: {e}")
            return ""
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

def get_pandoc_ast(filepath, doc_format):
    """Converts a document to Pandoc's JSON Abstract Syntax Tree."""
    try:
        json_str = pypandoc.convert_file(filepath, 'json', format=doc_format, extra_args=[f'--extract-media={config.REPORTS_DIR}/media'])
        return json.loads(json_str)
    except Exception as e:
        print(f"Error converting {filepath} to Pandoc AST: {e}")
        return None

def extract_special_blocks(filepath, doc_format):
    """
    Extracts content from specific blocks that should NOT be translated,
    e.g., code blocks, equations, figure paths.
    """
    content = {
        'code_blocks': [],
        'equations': [],
        'image_paths': [],
        'labels': {}, # {label_name: line_number}
        'references': [] # {ref_name: line_number}
    }
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if doc_format == 'latex':
        code_block_start = re.compile(r'\\begin\{(?:lstlisting|verbatim)\}')
        code_block_end = re.compile(r'\\end\{(?:lstlisting|verbatim)\}')
        equation_block_start = re.compile(r'\\begin\{(?:equation|align|$$)\}')
        equation_block_end = re.compile(r'\\end\{(?:equation|align|$$)\}')
        inline_math = re.compile(r'\$(.*?)\$')
        image_path = re.compile(r'\\includegraphics(?:\[.*?\])?\{(.*?)\}')
        label_pattern = re.compile(r'\\label\{(.*?)\}')
        ref_pattern = re.compile(r'\\ref\{(.*?)\}|\\eqref\{(.*?)\}|\\cite\{(.*?)\}')

        in_code = False
        in_equation = False
        current_block = []

        for i, line in enumerate(lines):
            if code_block_start.search(line):
                in_code = True
                current_block = [line]
            elif code_block_end.search(line) and in_code:
                in_code = False
                current_block.append(line)
                content['code_blocks'].append("".join(current_block))
                current_block = []
            elif equation_block_start.search(line):
                in_equation = True
                current_block = [line]
            elif equation_block_end.search(line) and in_equation:
                in_equation = False
                current_block.append(line)
                content['equations'].append("".join(current_block))
                current_block = []
            elif in_code or in_equation:
                current_block.append(line)
            else:
                # Normal line processing
                for match in inline_math.finditer(line):
                    content['equations'].append(f"${match.group(1)}$")
                for match in image_path.finditer(line):
                    content['image_paths'].append(match.group(1))
                for match in label_pattern.finditer(line):
                    content['labels'][match.group(1)] = i
                for match in ref_pattern.finditer(line):
                    # Pick the non-None group for ref/eqref/cite
                    ref_key = next((g for g in match.groups() if g is not None), None)
                    if ref_key:
                        content['references'].append({'key': ref_key, 'line': i})

    elif doc_format in ['markdown', 'myst']:
        # Markdown/Myst specific patterns (e.g., ``` code blocks, $ equations, ![alt](path) images)
        code_block_pattern = re.compile(r'```.*?```', re.DOTALL)
        math_block_pattern = re.compile(r'\$\$.*?\$\$', re.DOTALL)
        inline_math_pattern = re.compile(r'\$(.*?)\$')
        image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')

        text_content = "".join(lines)
        content['code_blocks'].extend(code_block_pattern.findall(text_content))
        content['equations'].extend(math_block_pattern.findall(text_content))
        content['equations'].extend(inline_math_pattern.findall(text_content))
        content['image_paths'].extend(image_pattern.findall(text_content))
        # TODO: Further parsing for Myst references 

    return content

import config # Import config here to avoid circular dependency if config imports parser


# Example usage:
# source_text = extract_natural_language_text('data/source/my_doc.tex', 'latex')
# source_ast = get_pandoc_ast('data/source/my_doc.tex', 'latex')
# special_blocks = extract_special_blocks('data/source/my_doc.tex', 'latex')
