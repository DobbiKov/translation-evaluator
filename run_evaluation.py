import os
import time
import json
from src import document_parser, nl_evaluator, struct_evaluator, rendering_evaluator, utils
import config

def evaluate_document_pair(source_path, llm_translated_path, human_ref_path, doc_format, lang_pair_codes):
    """Evaluates a single document pair across all selected metrics."""
    doc_id = os.path.splitext(os.path.basename(source_path))[0]
    results = {
        'document_id': doc_id,
        'source_format': doc_format,
        'source_lang': lang_pair_codes['source'],
        'target_lang': lang_pair_codes['target'],
        'nl_metrics': {},
        'structural_checks': {},
        'visual_metrics': {}
    }

    utils.log_message(f"--- Evaluating {doc_id} ({doc_format}) from {lang_pair_codes['source']} to {lang_pair_codes['target']} ---")

    # Natural Language Translation Quality
    source_text = document_parser.extract_natural_language_text(source_path, doc_format)
    llm_translated_text = document_parser.extract_natural_language_text(llm_translated_path, doc_format)

    if config.RUN_BLEU or config.RUN_TER or config.RUN_BERT_SCORE or config.RUN_COMET:
        if not human_ref_path:
            utils.log_message(f"Skipping NL metrics for {doc_id}: No human reference provided.", level='WARNING')
        else:
            human_ref_text = document_parser.extract_natural_language_text(human_ref_path, doc_format)
            if not human_ref_text:
                utils.log_message(f"Human reference text for {doc_id} is empty after extraction. Skipping NL metrics.", level='WARNING')
            elif not llm_translated_text:
                utils.log_message(f"LLM translated text for {doc_id} is empty after extraction. Skipping NL metrics.", level='WARNING')
            elif human_ref_text:
                if config.RUN_BLEU:
                    results['nl_metrics']['bleu'] = nl_evaluator.calculate_bleu(human_ref_text, llm_translated_text)
                if config.RUN_TER:
                    results['nl_metrics']['ter'] = nl_evaluator.calculate_ter(human_ref_text, llm_translated_text)
                if config.RUN_BERT_SCORE:
                    results['nl_metrics']['bert_score'] = nl_evaluator.calculate_bert_score(human_ref_text, llm_translated_text, lang=lang_pair_codes['target'])
                if config.RUN_COMET:
                    results['nl_metrics']['comet'] = nl_evaluator.calculate_comet(source_text, human_ref_text, llm_translated_text)
            else:
                utils.log_message(f"Could not extract text from human reference for {doc_id}. Skipping NL metrics.", level='WARNING')
    else:
        utils.log_message(f"No NL metrics enabled in config for {doc_id}.", level='INFO')


    # Structural Preservation Checks
    if config.RUN_AST_COMPARISON or config.RUN_PATTERN_MATCHING or config.RUN_REF_INTEGRITY:
        source_ast = document_parser.get_pandoc_ast(source_path, doc_format)
        llm_translated_ast = document_parser.get_pandoc_ast(llm_translated_path, doc_format)

        source_special_blocks = document_parser.extract_special_blocks(source_path, doc_format)
        llm_translated_special_blocks = document_parser.extract_special_blocks(llm_translated_path, doc_format)

        if source_ast and llm_translated_ast:
            if config.RUN_AST_COMPARISON:
                ast_diffs = struct_evaluator.compare_pandoc_asts(source_ast, llm_translated_ast)
                results['structural_checks']['ast_differences'] = ast_diffs
                results['structural_checks']['ast_diff_count'] = len(ast_diffs)
            if config.RUN_PATTERN_MATCHING:
                block_preservation = struct_evaluator.check_special_block_preservation(source_special_blocks, llm_translated_special_blocks)
                results['structural_checks']['special_block_preservation'] = block_preservation
                results['structural_checks']['special_block_issues_count'] = len(block_preservation)
            if config.RUN_REF_INTEGRITY:
                ref_integrity = struct_evaluator.check_reference_integrity(source_special_blocks, llm_translated_special_blocks)
                results['structural_checks']['reference_integrity'] = ref_integrity
                results['structural_checks']['reference_issues_count'] = len(ref_integrity)
        else:
            utils.log_message(f"Could not get ASTs for {doc_id}. Skipping structural checks.", level='WARNING')
    else:
        utils.log_message(f"No structural checks enabled in config for {doc_id}.", level='INFO')


    # Visual/Layout Comparison
    if config.RUN_VISUAL_DIFF and doc_format == 'latex': # Visual diff makes most sense for LaTeX
        output_sub_dir = os.path.join(config.REPORTS_DIR, doc_id)
        os.makedirs(output_sub_dir, exist_ok=True)

        source_pdf_path = rendering_evaluator.compile_latex_to_pdf(source_path, output_sub_dir)
        llm_pdf_path = rendering_evaluator.compile_latex_to_pdf(llm_translated_path, output_sub_dir)

        if source_pdf_path and llm_pdf_path:
            source_images = rendering_evaluator.convert_pdf_to_images(source_pdf_path, output_sub_dir)
            llm_images = rendering_evaluator.convert_pdf_to_images(llm_pdf_path, output_sub_dir)

            if source_images and llm_images:
                page_rmses = []
                num_pages = min(len(source_images), len(llm_images))
                results['visual_metrics']['page_count_source'] = len(source_images)
                results['visual_metrics']['page_count_llm'] = len(llm_images)
                
                for i in range(num_pages):
                    diff_img_path = os.path.join(output_sub_dir, f"{doc_id}_page{i+1}_diff.png")
                    rmse = rendering_evaluator.compare_images_visually(source_images[i], llm_images[i], diff_output_path=diff_img_path)
                    page_rmses.append({'page': i+1, 'rmse': rmse, 'diff_image': diff_img_path})
                results['visual_metrics']['page_rmse'] = page_rmses
                results['visual_metrics']['average_rmse'] = sum(p['rmse'] for p in page_rmses if p['rmse'] is not None) / len(page_rmses) if page_rmses else None
            else:
                utils.log_message(f"Could not convert PDFs to images for {doc_id}. Skipping visual diff.", level='WARNING')
        else:
            utils.log_message(f"Could not compile LaTeX to PDF for {doc_id}. Skipping visual diff.", level='WARNING')
    elif config.RUN_VISUAL_DIFF:
        utils.log_message(f"Visual diff is currently only implemented for LaTeX. Skipping for {doc_format} and {doc_id}.", level='INFO')
    else:
        utils.log_message(f"No visual diff enabled in config for {doc_id}.", level='INFO')

    utils.log_message(f"--- Finished evaluating {doc_id} ---")
    return results

def main():
    all_results = []
    start_time = time.time()
    utils.log_message("Starting evaluation process...")

    for lang_pair in config.LANG_PAIRS:
        src_lang = lang_pair['source']
        tgt_lang = lang_pair['target']

        for doc_format in config.DOC_FORMATS:
            source_files = document_parser.get_document_paths(config.SOURCE_DIR, src_lang, doc_format)
            
            for source_file in source_files:
                doc_id = os.path.splitext(os.path.basename(source_file))[0]
                
                # Construct paths for translated and reference files based on naming convention
                llm_translated_file = os.path.join(config.LLM_TRANSLATED_DIR, f"{doc_id}_{tgt_lang}{os.path.splitext(source_file)[1]}")
                
                human_ref_file = None
                if os.path.exists(config.HUMAN_REFERENCE_DIR):
                    human_ref_file = os.path.join(config.HUMAN_REFERENCE_DIR, f"{doc_id}_{tgt_lang}{os.path.splitext(source_file)[1]}")
                    if not os.path.exists(human_ref_file):
                        human_ref_file = None # No human reference found

                if not os.path.exists(llm_translated_file):
                    utils.log_message(f"LLM translated file not found for {doc_id} ({tgt_lang}, {doc_format}). Skipping.", level='WARNING')
                    continue
                
                result = evaluate_document_pair(source_file, llm_translated_file, human_ref_file, doc_format, {'source': src_lang, 'target': tgt_lang})
                all_results.append(result)

    # Save overall results
    results_filename = f"evaluation_results_{time.strftime('%Y%m%d-%H%M%S')}.json"
    utils.save_json_report(all_results, results_filename)

    nl_summary_data = []
    for res in all_results:
        summary = {
            'document_id': res['document_id'],
            'source_format': res['source_format'],
            'source_lang': res['source_lang'],
            'target_lang': res['target_lang'],
            'bleu': res['nl_metrics'].get('bleu'),
            'ter': res['nl_metrics'].get('ter'),
            'bert_score': res['nl_metrics'].get('bert_score'),
            'comet': res['nl_metrics'].get('comet'),
            'ast_diff_count': res['structural_checks'].get('ast_diff_count'),
            'special_block_issues_count': res['structural_checks'].get('special_block_issues_count'),
            'reference_issues_count': res['structural_checks'].get('reference_issues_count'),
            'average_rmse': res['visual_metrics'].get('average_rmse')
        }
        nl_summary_data.append(summary)
    
    summary_fieldnames = list(nl_summary_data[0].keys()) if nl_summary_data else []
    summary_filename = f"evaluation_summary_{time.strftime('%Y%m%d-%H%M%S')}.csv"
    utils.save_csv_report(nl_summary_data, summary_filename, summary_fieldnames)

    end_time = time.time()
    utils.log_message(f"Evaluation complete. Total time: {end_time - start_time:.2f} seconds.")

if __name__ == '__main__':
    main()
