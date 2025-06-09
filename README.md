# Translation Evaluator

A python tool to evaluate machine translation. The tool evaluates:
- the Natural Language (NL) translation quality
- structure preserving quality

It supports common metrics (BLEU, chrF, TER) as well as recent neural metrics (BERTScore, COMET).

## Installation
1. Clone the repository:
```sh
git clone https://github.com/DobbiKov/translation-evaluator.git
cd translation-evaluator
```
2. Create the environment (with `conda`)
```sh
conda env create -f environment.yml 
```

## How to Use and Expand
1. Activate the environment (with `conda`)
    ```sh
    conda activate doc_eval_env
    ```

2. Populate `data/`:
    - Place your original scientific documents in `data/source/`.
    - Place the LLM-translated versions (with `_lang_code` suffix in filename, e.g., `my_doc_de.tex`) in `data/llm_translated/`.
    - (Optional but recommended for NL metrics) Place human-translated reference versions in data/human_reference/. (also with the `_lang_code`)

3. Configure `config.py`:
    - Adjust `LANG_PAIRS`, `DOC_FORMATS`.
    - Enable/disable specific metrics (`RUN_BLEU`, `RUN_AST_COMPARISON`, etc.) based on your needs.
    - Set `PANDOC_PATH` if **pandoc** isn't in your system's **PATH**.

4. Run `run_evaluation.py`:
```py
python3 run_evaluation.py
```

5. Review Reports:
- Check `reports/evaluation_results_*.json` for detailed results.
- Check `reports/evaluation_summary_*.csv` for a quick overview of NL and structural counts.
- For LaTeX visual diffs, look in `reports/<doc_id>/` for generated PDFs and diff images.
