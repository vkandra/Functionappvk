# Use a Python 3.8 base image
FROM python:3.8

# Create a working directory for your application
WORKDIR /app

# Install required libraries
RUN pip install azure-functions azure-cosmos azure-storage-blob pandas numpy

# Copy your code files
COPY __init__.py /app
COPY requirements.txt /app

# Set environment variables for CosmosDB and Blob Storage
#ENV COSMOSDB_ENDPOINT="https://cosmostextextract.documents.azure.com:443/"
#ENV COSMOSDB_KEY="RDzX0ACzpvaRKVpUQKE3kVr9ZYtoOiOMSS7sPqURb5mZ3F991BJ0RTMDmjIFWkdJ3cB7pr59vP9MACDbAMe9qA=="
#ENV BLOB_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=texextraction;AccountKey=5K34D7lHOov+QQKXSOC3e8g521QG63T5Qqbab+ql2ZBAjZU2RU0ePiEDREePRWPqm1Msw4n/VG7++AStBZMRSQ==;EndpointSuffix=core.windows.net"

# Set the entrypoint to your application
ENTRYPOINT ["python","__init__.py"]
