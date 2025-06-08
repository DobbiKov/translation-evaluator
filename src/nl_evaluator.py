import sacrebleu
from bert_score import score as bert_score_calc
from comet import download_model, load_from_checkpoint

def calculate_bleu(reference_text, hypothesis_text):
    """Calculates BLEU score."""
    return sacrebleu.sentence_bleu(hypothesis_text, [reference_text]).score

def calculate_ter(reference_text, hypothesis_text):
    """Calculates TER score."""
    return sacrebleu.sentence_ter(hypothesis_text, [reference_text]).score

def calculate_bert_score(reference_text, hypothesis_text, lang='en'):
    """Calculates BERTScore."""
    P, R, F1 = bert_score_calc([hypothesis_text], [[reference_text]], lang=lang, verbose=False)
    return F1.mean().item()

def calculate_comet(source_text, reference_text, hypothesis_text):
    """
    Calculates COMET score.
    Requires downloading a COMET model, e.g., 'Unbabel/wmt22-comet-da'.
    """
    try:
        model_path = download_model("Unbabel/wmt22-comet-da")
        model = load_from_checkpoint(model_path)

        data = [{'src': source_text, 'mt': hypothesis_text, 'ref': reference_text}]
        return model.predict(data)["scores"][0]

    except Exception as e:
        print(f"Error calculating COMET: {e}")
        return None
