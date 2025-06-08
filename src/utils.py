import os
import json
import csv

def save_json_report(data, filename, directory=None):
    """Saves data to a JSON file."""
    if directory is None:
        directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Report saved to {filepath}")

def save_csv_report(data, filename, fieldnames, directory=None):
    """Saves data to a CSV file."""
    if directory is None:
        directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Report saved to {filepath}")

def log_message(message, level='INFO'):
    """Logs messages to a file and console."""
    import datetime
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'evaluation.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now().isoformat()} - {level}: {message}\n")
    print(f"{level}: {message}")
