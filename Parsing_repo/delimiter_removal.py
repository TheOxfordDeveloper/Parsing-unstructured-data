import os
import re

# File paths
input_file = "/Users/theoxforddevelopr/Desktop/Parsing_repo/raw_data/Abadan_raw.txt"
output_directory = "/Users/theoxforddeveloper/Desktop/Parsing_repo/removed_delimiter_data"
output_file = os.path.join(output_directory, "Abadan_delimiter.txt")

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Read the input file
with open(input_file, "r") as file:
    data = file.readlines()

# Process the data
processed_data = []
for line in data:
    # Replace delimiters with commas
    line = (
        line.replace(" by ", ", ")
        .replace("-", ", ")
        .replace("\t", ", ")
        .replace("...", ", ")
        .replace(".", ", ")
        .replace("•", ", ")
    )
    
    # Replace consecutive commas with a single comma
    line = re.sub(r",\s*,", ",", line)
    
    processed_data.append(line)

# Write the processed data to the output file
with open(output_file, "w") as file:
    file.write("".join(processed_data))

print(f"Processed data saved to {output_file}")

