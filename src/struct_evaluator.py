import json
import re

def compare_pandoc_asts(source_ast, target_ast, sensitivity='high'):
    """
    Compares two Pandoc ASTs recursively.
    Identifies differences in structure (missing/extra/changed nodes)
    and content (for non-text nodes that should be preserved).
    """
    differences = []

    def _compare_node(path, node1, node2):
        nonlocal differences

        if node1 is None and node2 is None:
            return
        elif node1 is None:
            differences.append({'path': path, 'type': 'extra_node', 'target_node': node2})
            return
        elif node2 is None:
            differences.append({'path': path, 'type': 'missing_node', 'source_node': node1})
            return

        # Check node type
        if node1.get('t') != node2.get('t'):
            differences.append({'path': path, 'type': 'type_mismatch', 'source_type': node1.get('t'), 'target_type': node2.get('t')})
            return

        node_type = node1.get('t')

        # Handle specific node types
        if node_type == 'Str' or node_type == 'Code' or node_type == 'RawBlock':
            # For Str, we expect text to be translated.
            # For Code/RawBlock, we expect exact preservation.
            if node_type in ['Code', 'RawBlock'] and node1.get('c') != node2.get('c'):
                 differences.append({'path': path, 'type': f'content_mismatch_{node_type}', 'source_content': node1.get('c'), 'target_content': node2.get('c')})
        elif node_type == 'Image':
            # Check if image path (second element of 'c' list) is preserved
            if len(node1['c']) > 1 and len(node2['c']) > 1 and node1['c'][1] != node2['c'][1]:
                differences.append({'path': path, 'type': 'image_path_mismatch', 'source_path': node1['c'][1], 'target_path': node2['c'][1]})
        elif node_type in ['Math', 'DisplayMath', 'InlineMath']:
            # Math content 'c' should be identical
            if node1['c'][1] != node2['c'][1]:
                differences.append({'path': path, 'type': 'math_mismatch', 'source_math': node1['c'][1], 'target_math': node2['c'][1]})
        elif node_type in ['Link', 'Citation']:
            # Check target/key preservation
            if node1['c'][2] != node2['c'][2]: # Link target
                differences.append({'path': path, 'type': 'link_target_mismatch', 'source': node1['c'][2], 'target': node2['c'][2]})
            if node1['c'][0] != node2['c'][0]: # Citation ID/key
                 differences.append({'path': path, 'type': 'citation_key_mismatch', 'source': node1['c'][0], 'target': node2['c'][0]})


        # Recurse on children if 'c' key exists and is a list
        if 'c' in node1 and isinstance(node1['c'], list) and 'c' in node2 and isinstance(node2['c'], list):
            min_len = min(len(node1['c']), len(node2['c']))
            for i in range(min_len):
                _compare_node(f"{path}.c[{i}]", node1['c'][i], node2['c'][i])
            if len(node1['c']) > len(node2['c']):
                for i in range(min_len, len(node1['c'])):
                    differences.append({'path': f"{path}.c[{i}]", 'type': 'missing_child', 'source_node': node1['c'][i]})
            elif len(node2['c']) > len(node1['c']):
                for i in range(min_len, len(node2['c'])):
                    differences.append({'path': f"{path}.c[{i}]", 'type': 'extra_child', 'target_node': node2['c'][i]})
        elif 'c' in node1 and 'c' in node2 and node1['c'] != node2['c']:
             # For other 'c' types (e.g., string attributes), direct comparison
            differences.append({'path': path, 'type': 'attribute_mismatch_c', 'source_attr': node1['c'], 'target_attr': node2['c']})


        if node_type == 'Header' and (node1['c'][0] != node2['c'][0]): # Header level
            differences.append({'path': path, 'type': 'header_level_mismatch', 'source_level': node1['c'][0], 'target_level': node2['c'][0]})
        if node_type == 'List' and (node1['c'][0][0]['t'] != node2['c'][0][0]['t']): # List type (BulletList vs OrderedList)
            differences.append({'path': path, 'type': 'list_type_mismatch', 'source_type': node1['c'][0][0]['t'], 'target_type': node2['c'][0][0]['t']})


    _compare_node("root", source_ast, target_ast)
    return differences

def check_special_block_preservation(source_blocks, target_blocks):
    """
    Compares extracted special blocks for identity.
    `source_blocks` and `target_blocks` are dictionaries from `extract_special_blocks`.
    """
    results = []

    # Code blocks
    if len(source_blocks['code_blocks']) != len(target_blocks['code_blocks']):
        results.append({"type": "code_block_count_mismatch", "source_count": len(source_blocks['code_blocks']), "target_count": len(target_blocks['code_blocks'])})
    else:
        for i, (s_block, t_block) in enumerate(zip(source_blocks['code_blocks'], target_blocks['code_blocks'])):
            if s_block != t_block:
                results.append({"type": "code_block_content_mismatch", "index": i, "source_content": s_block, "target_content": t_block})

    # Equations
    if len(source_blocks['equations']) != len(target_blocks['equations']):
        results.append({"type": "equation_count_mismatch", "source_count": len(source_blocks['equations']), "target_count": len(target_blocks['equations'])})
    else:
        for i, (s_eq, t_eq) in enumerate(zip(source_blocks['equations'], target_blocks['equations'])):
            if s_eq != t_eq: # Simple string comparison for math markup
                results.append({"type": "equation_content_mismatch", "index": i, "source_content": s_eq, "target_content": t_eq})

    # Image paths (check if they are preserved and not translated)
    if set(source_blocks['image_paths']) != set(target_blocks['image_paths']):
        results.append({"type": "image_path_set_mismatch", "source_paths": list(source_blocks['image_paths']), "target_paths": list(target_blocks['image_paths'])})

    return results

def check_reference_integrity(source_blocks, target_blocks):
    """
    Checks if labels and references are preserved and consistent.
    Assumes `source_blocks['labels']` and `target_blocks['labels']` contain dicts of {key: line_number}.
    Assumes `source_blocks['references']` and `target_blocks['references']` contain lists of {key: line_number}.
    """
    results = []

    # Check label preservation (keys should be identical)
    source_label_keys = set(source_blocks['labels'].keys())
    target_label_keys = set(target_blocks['labels'].keys())

    missing_labels_in_target = list(source_label_keys - target_label_keys)
    extra_labels_in_target = list(target_label_keys - source_label_keys)

    if missing_labels_in_target:
        results.append({"type": "missing_labels", "labels": missing_labels_in_target})
    if extra_labels_in_target:
        results.append({"type": "extra_labels", "labels": extra_labels_in_target})

    # Check reference preservation (keys should be identical, and ideally point to existing labels)
    source_ref_keys = [ref['key'] for ref in source_blocks['references']]
    target_ref_keys = [ref['key'] for ref in target_blocks['references']]

    # Simple count mismatch
    if len(source_ref_keys) != len(target_ref_keys):
        results.append({"type": "reference_count_mismatch", "source_count": len(source_ref_keys), "target_count": len(target_ref_keys)})

    for i, s_ref_key in enumerate(source_ref_keys):
        if i < len(target_ref_keys) and s_ref_key != target_ref_keys[i]:
            results.append({"type": "reference_key_mismatch", "index": i, "source_key": s_ref_key, "target_key": target_ref_keys[i]})
        elif i >= len(target_ref_keys):
            results.append({"type": "missing_reference_in_target", "source_key": s_ref_key})

    # Check if target references point to non-existent labels in the target document
    for ref in target_blocks['references']:
        if ref['key'] not in target_label_keys:
            results.append({"type": "dangling_reference", "key": ref['key'], "line": ref['line']})

    return results

import config 
