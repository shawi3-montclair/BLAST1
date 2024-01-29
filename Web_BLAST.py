import requests
from urllib.parse import quote
import time
import sys

# Check if enough arguments are provided
if len(sys.argv) < 4:
    print("usage: web_blast.py program database query [query]...")
    print("where program = megablast, blastn, blastp, rpsblast, blastx, tblastn, tblastx\n")
    print("example: web_blast.py blastp nr protein.fasta")
    print("example: web_blast.py rpsblast cdd protein.fasta")
    print("example: web_blast.py megablast nt dna1.fasta dna2.fasta")
    sys.exit(1)

program = sys.argv[1]
database = sys.argv[2]

# Adjust program for specific cases
if program == "megablast":
    program = "blastn&MEGABLAST=on"
elif program == "rpsblast":
    program = "blastp&SERVICE=rpsblast"

# Read and encode the queries
encoded_query = ""
for query_file in sys.argv[3:]:
    with open(query_file, 'r') as file:
        for line in file:
            encoded_query += quote(line)

# Build and send the request
args = f"CMD=Put&PROGRAM={program}&DATABASE={database}&QUERY={encoded_query}"
response = requests.post('https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi', 
                         data=args, 
                         headers={'Content-Type': 'application/x-www-form-urlencoded'})

# Parse out the request id and estimated time to completion
content = response.text
rid = [line for line in content.split('\n') if line.startswith('    RID = ')][0].split('=')[1].strip()
rtoe = int([line for line in content.split('\n') if line.startswith('    RTOE = ')][0].split('=')[1].strip())

# Wait for search to complete
time.sleep(rtoe)

# Poll for results
while True:
    time.sleep(5)
    response = requests.get(f"https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi?CMD=Get&FORMAT_OBJECT=SearchInfo&RID={rid}")
    content = response.text

    if 'Status=WAITING' in content:
        continue
    elif 'Status=FAILED' in content:
        print(f"Search {rid} failed; please report to blast-help@ncbi.nlm.nih.gov.")
        sys.exit(4)
    elif 'Status=UNKNOWN' in content:
        print(f"Search {rid} expired.")
        sys.exit(3)
    elif 'Status=READY' in content:
        if 'ThereAreHits=yes' in content:
            break
        else:
            print("No hits found.")
            sys.exit(2)

# Retrieve and display results
response = requests.get(f"https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi?CMD=Get&FORMAT_TYPE=Text&RID={rid}")
print(response.text)
sys.exit(0)
