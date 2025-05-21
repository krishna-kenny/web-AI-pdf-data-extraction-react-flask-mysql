import boto3
import time
import os
import csv

# ── CONFIGURATION ──────────────────────────────────────────────────────
AWS_REGION         = "ap-south-1"
S3_BUCKET          = "cargofl-ai-invoice-reader-test"
DOCUMENT_KEY       = "FTL_Bill.pdf"             # S3 key for the PDF
OUTPUT_DIR         = "./textract_tables"        # Local directory to save CSVs
POLL_INTERVAL      = 5                          # Seconds between polling Textract
# ───────────────────────────────────────────────────────────────────────

# —— SETUP CLIENTS ——  
textract = boto3.client("textract", region_name=AWS_REGION)

def start_table_detection(bucket, key):
    resp = textract.start_document_analysis(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["TABLES"]
    )
    return resp["JobId"]

def is_job_complete(job_id):
    resp = textract.get_document_analysis(JobId=job_id)
    return resp["JobStatus"], resp

def get_all_results(job_id):
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
    blocks = []
    for page in pages:
        blocks.extend(page["Blocks"])
    block_map = {b["Id"]: b for b in blocks}
    tables = [b for b in blocks if b["BlockType"] == "TABLE"]

    all_tables = []

    for table in tables:
        cells = []
        for rel in table.get("Relationships", []):
            if rel["Type"] == "CHILD":
                for cid in rel["Ids"]:
                    cell = block_map[cid]
                    if cell["BlockType"] == "CELL":
                        cells.append(cell)

        max_row = max(cell["RowIndex"] for cell in cells)
        max_col = max(cell["ColumnIndex"] for cell in cells)
        grid = [["" for _ in range(max_col)] for _ in range(max_row)]

        for cell in cells:
            text = ""
            for rel in cell.get("Relationships", []):
                if rel["Type"] == "CHILD":
                    for tid in rel["Ids"]:
                        item = block_map[tid]
                        if item["BlockType"] == "WORD":
                            text += item["Text"] + " "
                        elif item["BlockType"] == "SELECTION_ELEMENT" and item["SelectionStatus"] == "SELECTED":
                            text += "X "
            grid[cell["RowIndex"] - 1][cell["ColumnIndex"] - 1] = text.strip()

        all_tables.append(grid)
    return all_tables

def save_tables_to_csv(tables, outdir):
    os.makedirs(outdir, exist_ok=True)
    for tbl_idx, grid in tables:
        csv_path = os.path.join(outdir, f"table_{tbl_idx}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in grid:
                writer.writerow(row)
        print(f"[INFO] Wrote Table {tbl_idx} → {csv_path}")

def main():
    try:
        print("[INFO] Starting Textract TABLE analysis job...")
        job_id = start_table_detection(S3_BUCKET, DOCUMENT_KEY)
        print(f"[INFO] Job started. JobId: {job_id}")

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
    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")

if __name__ == "__main__":
    main()
