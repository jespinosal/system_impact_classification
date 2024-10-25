"""
Steps offline:
1. Load/parse documents on unique table
2. Build group names
3. Perform aggregation based on group names and save "agg table" in disc.

Steps Online:
1. Load "agg table" on the system prompt. (use RAG in future having more equipments)
2. Ask to customer for equipment and report question 1 to 7.
3. Check questions 8a and 8b if they are false jump to step 5 else start tree based question
4. Run tree based question 
5. Provide final feedback
"""