.PHONY: all
all: test

# Set the input and output file names
INPUT_FILE = test.in
OUTPUT_FILE = out.txt

# Define the Python interpreter (adjust as needed)
PYTHON = python3

print: 
	$(PYTHON) 431proj1.py

test:
	$(PYTHON) 431proj1.py $(INPUT_FILE) > $(OUTPUT_FILE)

clean:
	rm -f $(OUTPUT_FILE)