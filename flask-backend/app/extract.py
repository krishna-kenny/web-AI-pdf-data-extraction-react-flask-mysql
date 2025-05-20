import boto3
import time
import os
import csv

# ── CONFIGURATION CONSTANTS ─────────────────────────────────────────────
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN     = None               # or "YOUR_SESSION_TOKEN" if needed
AWS_REGION            = "ap-south-1"

S3_BUCKET        = "cargofl-ai-invoice-reader-test"      # replace with your bucket
DOCUMENT_KEY     = "FTL_Bill.pdf"      # S3 key for the PDF
OUTPUT_DIR       = "./textract_tables"     # local dir to write CSVs
POLL_INTERVAL    = 5                       # seconds between status checks
# ────────────────────────────────────────────────────────────────────────

# —— SETUP CLIENT ——  
textract = boto3.client(
    "textract",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

def start_table_detection(bucket, key):
    """Starts an async Textract job to detect TABLES."""
    resp = textract.start_document_analysis(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["TABLES"]
    )
    return resp["JobId"]

def is_job_complete(job_id):
    """Checks Textract job status."""
    resp = textract.get_document_analysis(JobId=job_id)
    return resp["JobStatus"], resp

def get_all_results(job_id):
    """Retrieves paginated results."""
    pages = []
    next_token = None

    while True:
        if next_token:
            resp = textract.get_document_analysis(JobId=job_id, NextToken=next_token)
        else:
            resp = textract.get_document_analysis(JobId=job_id)
        pages.append(resp)
        next_token = resp.get("NextToken")
        if not next_token:
            break
    return pages

def extract_tables(pages):
    """
    From Textract response pages, yield each table as a list of rows,
    where each row is a list of cell texts in column order.
    """
    # collect all blocks
    blocks = []
    for page in pages:
        blocks.extend(page["Blocks"])

    # index blocks by Id for lookups
    block_map = {b["Id"]: b for b in blocks}

    # find table blocks
    tables = [b for b in blocks if b["BlockType"] == "TABLE"]

    for tbl_idx, table in enumerate(tables, start=1):
        # find cell blocks that belong to this table
        cell_blocks = []
        for rel in table.get("Relationships", []):
            if rel["Type"] == "CHILD":
                for cid in rel["Ids"]:
                    cb = block_map[cid]
                    if cb["BlockType"] == "CELL":
                        cell_blocks.append(cb)

        # determine max row/col to size the grid
        max_row = max(cb["RowIndex"] for cb in cell_blocks)
        max_col = max(cb["ColumnIndex"] for cb in cell_blocks)

        # initialize empty grid
        grid = [["" for _ in range(max_col)] for __ in range(max_row)]

        # fill grid
        for cb in cell_blocks:
            # get text inside the cell
            text = ""
            for crel in cb.get("Relationships", []):
                if crel["Type"] == "CHILD":
                    for tid in crel["Ids"]:
                        tb = block_map[tid]
                        if tb["BlockType"] == "WORD":
                            text += tb["Text"] + " "
                        elif tb["BlockType"] == "SELECTION_ELEMENT" and tb["SelectionStatus"] == "SELECTED":
                            text += "X "
            text = text.strip()

            # place in grid (row/col indexes are 1-based)
            r = cb["RowIndex"] - 1
            c = cb["ColumnIndex"] - 1
            grid[r][c] = text

        yield tbl_idx, grid

def save_tables_to_csv(tables, outdir):
    """Write each table grid to its own CSV file."""
    os.makedirs(outdir, exist_ok=True)
    for tbl_idx, grid in tables:
        csv_path = os.path.join(outdir, f"table_{tbl_idx}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in grid:
                writer.writerow(row)
        print(f"[INFO] Wrote Table {tbl_idx} → {csv_path}")

def main():
    print("[INFO] Starting Textract TABLE analysis job...")
    job_id = start_table_detection(S3_BUCKET, DOCUMENT_KEY)
    print(f"[INFO] Job started. JobId: {job_id}")

    # wait for completion
    while True:
        status, resp = is_job_complete(job_id)
        print(f"[INFO] Job status: {status}")
        if status in ("SUCCEEDED", "FAILED"):
            break
        time.sleep(POLL_INTERVAL)

    if status == "SUCCEEDED":
        print("[INFO] Job succeeded; fetching results...")
        pages = get_all_results(job_id)
        tables = list(extract_tables(pages))
        if tables:
            save_tables_to_csv(tables, OUTPUT_DIR)
            print(f"[INFO] Extracted {len(tables)} table(s).")
        else:
            print("[WARN] No tables found in document.")
    else:
        print(f"[ERROR] Textract job failed: {resp}")

if __name__ == "__main__":
    main()
