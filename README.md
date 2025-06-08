# Translation Evaluation

A python tool to evaluate machine translation. The tool evaluates:
- the Natural Language (NL) translation quality
- structure preserving quality

## Structure for the data to evaluate
Place the original documents into `data/source/` and the translated documents with the same names except add `_<lang_code>` to the file name, into the `data/llm_translated` directory.

Example:
Put `main.tex` into `data/source` (`data/source/main.tex`) and then the translated file into `data/llm_translated` (`data/llm_translated/main_de.tex`) for German translation.

## How to Use and Expand

1. Populate `data/`:
    - Place your original scientific documents in `data/source/`.
    - Place the LLM-translated versions (with `_lang_code` suffix in filename, e.g., `my_doc_de.tex`) in `data/llm_translated/`.
    - (Optional but recommended for NL metrics) Place human-translated reference versions in data/human_reference/.

2. Configure `config.py`:
    - Adjust `LANG_PAIRS`, `DOC_FORMATS`.
    - Enable/disable specific metrics (`RUN_BLEU`, `RUN_AST_COMPARISON`, etc.) based on your needs.
    - Set `PANDOC_PATH` if **pandoc** isn't in your system's **PATH**.

3. Run `run_evaluation.py`:
```py
python3 run_evaluation.py
```
4. Review Reports:
- Check `reports/evaluation_results_*.json` for detailed results.
- Check `reports/evaluation_summary_*.csv` for a quick overview of NL and structural counts.
- For LaTeX visual diffs, look in `reports/<doc_id>/` for generated PDFs and diff images.
