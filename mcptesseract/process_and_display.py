#!/usr/bin/env python3

import sys
sys.path.append('.')

from server.tesseract import process_ground_truth_folder, display_all_bibliography_entries

def main():
    # First process the ground truth data
    print("Processing ground truth data...")
    result = process_ground_truth_folder("../ground_truth")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Then display all entries
    print("Displaying all entries (compact format)...")
    print(display_all_bibliography_entries(format="compact"))
    print("\nDisplaying all entries (detailed format)...")
    print(display_all_bibliography_entries(format="detailed"))

if __name__ == "__main__":
    main() 