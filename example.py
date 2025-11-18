from docstrange import DocumentExtractor

file_path = "sample_documents/invoice.pdf"

extractor = DocumentExtractor()

result = extractor.extract(file_path).extract_data(specified_fields=[
        "total_amount", 
        "date", 
        "vendor_name",
        "invoice_number"
    ])

print(result)
















exit()




print("📝=============================== JSON Output:===============================")
result = extractor.extract(file_path).extract_data()
print(result)




print("\n📝=============================== Specific Field :===============================")
result = extractor.extract(file_path)
specific_fields = result.extract_data(specified_fields=[
        "total_amount", 
        "date", 
        "vendor_name",
        "invoice_number"
    ])
print(specific_fields)



print("\n📝=============================== JSON Schema Extraction:===============================")
schema = {
        "invoice_number": "string",
        "total_amount": "number",
        "vendor_name": "string", 
        "items": [{
            "description": "string",
            "amount": "number"
        }]
    }
    
structured_data = result.extract_data(json_schema=schema)
print(structured_data)