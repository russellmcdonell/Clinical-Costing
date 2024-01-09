rm *.py
ln ../*.py .
ln ../tools/*.py .
python3 -m mkdocs build -c
