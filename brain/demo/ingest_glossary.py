#!/usr/bin/env python3

import sys
import requests
import os

def main():
    if len(sys.argv) != 2:
        print("Usage: python ingest_glossary.py <glossary_file>")
        sys.exit(1)
    
    glossary_file = sys.argv[1]
    api_url = os.environ.get('BRAIN_API_URL', 'http://localhost:8000/ingest')

    try:
        with open(glossary_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) < 2:
                    parts = line.split(',')
                    if len(parts) < 2:
                        print(f"Skipping invalid line: {line}")
                        continue
                term = parts[0].strip()
                definition = parts[1].strip()
                data = {
                    "term": term,
                    "definition": definition
                }
                response = requests.post(api_url, json=data)
                if response.status_code == 200:
                    print(f"Ingested term: {term}")
                else:
                    print(f"Failed to ingest {term}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
