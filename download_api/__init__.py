import azure.functions as func
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import pandas as pd
import io
import json
import os
import numpy as np
 
 
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Retrieve user_id and template_id from the request body or use default values
        req_body = req.get_json()
        user_id = req_body.get('user_id')
        sub_template_id = req_body.get('template_id')
 
        #clear the container before enerating the new excel
        clear_template_download_container()
        #call the cosmos function to get the url of generted excel
        blob_url = get_data_from_cosmos(user_id, sub_template_id)
 
        return func.HttpResponse(json.dumps({"blob_url": blob_url}), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)
def get_data_from_cosmos(user_id, sub_template_id):
    # Your Cosmos DB connection details
    endpoint = "https://cosmostextextract.documents.azure.com:443/"
    key = "RDzX0ACzpvaRKVpUQKE3kVr9ZYtoOiOMSS7sPqURb5mZ3F991BJ0RTMDmjIFWkdJ3cB7pr59vP9MACDbAMe9qA=="
    # Initialize Cosmos Client
    client = CosmosClient(endpoint, key)
    database_name = "TextExtraction"
 
    #DOCUMENT_DETAILS_MAIN_TABLE
    container_ddmt = "DocumentDetailsMainTable"
    # Get database and container client
    database_ddmt = client.get_database_client(database_name)
    container1 = database_ddmt.get_container_client(container_ddmt)
 
    #FILEWISE_OUTPUT
    container_FileWiseOutput = "FileWiseOutput"
    # Get database and container client
    database_FileWiseOutput = client.get_database_client(database_name)
    container2 = database_FileWiseOutput.get_container_client(container_FileWiseOutput)
 
    #FILEWISE_OUTPUT
    container_TD = "TemplateDetails"
    # Get database and container client
    database_TD = client.get_database_client(database_name)
    container3 = database_TD.get_container_client(container_TD)
 
    # Query data
    query = "SELECT * FROM c"
 
    file_list = list(container1.query_items(query, enable_cross_partition_query=True))
    data_list = list(container2.query_items(query, enable_cross_partition_query=True))
    template_list = list(container3.query_items(query, enable_cross_partition_query=True))
 
    d_id=[]
    d_name = []
    for item in template_list:
        if 'user_id' in item and item['user_id'] == user_id:
            if 'sub_template_id' in item and item['sub_template_id'] == sub_template_id:
                #sub_template_ID = item.get('sub_template_id') 
                customer_name = item.get('customer_name')
                department_name = item.get('department_name') 
                project_name = item.get('project_name') 
                sub_template = item.get('sub_template')
                r = [customer_name,department_name,project_name,sub_template]
    print(r)
    for item in file_list:
        if 'SubTemplateID' in item and item['SubTemplateID'] == sub_template_id:
            #if 'SubTemplateID' in item and item['SubTemplateID'] == sub_template_ID:
            document_id = item.get('DocumentID')
            d_id.append(document_id)
            document_name = item.get('DocumentName')
            d_name.append(document_name)
    print(d_id)
    print(d_name)
    docs = {key: value for key, value in zip(d_id, d_name)}
    print(docs)
    df = []
    for item in data_list:
        dd = pd.DataFrame()
        if 'doc_id' in item and item['doc_id'] in d_id:
            d = item['doc_id']
            docname = docs[d]
            for i in item['output']:
                input_val = i['excel_key']
                if i['map_cytext_value']  !='':
                    output_val = i['map_cytext_value']
                else:
                    output_val = i['prompt_value']
                if i['Confidence_Score'] == '':
                    conf_score=''
                else:
                    conf_score = i['Confidence_Score']
                if i['selection'] =='':
                    source =''
                else:
                    source = i['selection']
                c = "Confidence_Score_"+input_val
                s = "Source_"+input_val
                dd["Document Name"] = [docname]
                dd[input_val] = [output_val]
                dd[c] = [conf_score]
                dd[s] = [source]
            df.append(dd)
 
    print(df)
    #Concatenate the DataFrames into a single DataFrame if needed
    resulting_df = pd.concat(df, ignore_index=True)            
    column_names = resulting_df.columns.tolist()
    column_names = ['Customer Name','Department Name','Project Name','Sub Template'] + column_names
 
    # Create a new DataFrame to store the result
    result_df = pd.DataFrame()
 
    # Iterate through rows in the original DataFrame and list_row, and insert them side by side
    for index, row in resulting_df.iterrows():
        result_row = r + list(row)
        result_df = pd.concat([result_df, pd.DataFrame([result_row])], ignore_index=True)
    result_df.columns = column_names
    print(result_df)
    # Save filtered DataFrame to Excel
    excel_buffer = io.BytesIO()
    result_df.to_excel(excel_buffer, index=False)
    # Upload the file to Azure Blob Storage without storing in local
    excel_buffer.seek(0)  # Reset the buffer position to the beginning
 
    file_name = sub_template
    #Upload the Excel file to Azure Blob Storage
    download_url = upload_to_blob_storage(file_name, excel_buffer)
 
    return (download_url)
    # Function for file saving in Azure Blob Storage
def upload_to_blob_storage(file_name, content):
    connection_string = "DefaultEndpointsProtocol=https;AccountName=texextraction;AccountKey=5K34D7lHOov+QQKXSOC3e8g521QG63T5Qqbab+ql2ZBAjZU2RU0ePiEDREePRWPqm1Msw4n/VG7++AStBZMRSQ==;EndpointSuffix=core.windows.net"
    container_name = "template-download"
    blob_name = f"{file_name}.xlsx"
    download_link=f"https://texextraction.blob.core.windows.net/template-download/{blob_name}"
 
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
 
    with content as data:
        blob_client.upload_blob(data, overwrite=True)
        return(download_link)
 
def clear_template_download_container():
    # Define your Azure Storage connection string and container name
    connection_string = "DefaultEndpointsProtocol=https;AccountName=texextraction;AccountKey=5K34D7lHOov+QQKXSOC3e8g521QG63T5Qqbab+ql2ZBAjZU2RU0ePiEDREePRWPqm1Msw4n/VG7++AStBZMRSQ==;EndpointSuffix=core.windows.net"
    container_name = "template-download"
 
    try:
        # Create a BlobServiceClient using the connection string
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        # Create a ContainerClient for the specified container
        container_client = blob_service_client.get_container_client(container_name)
        # List all blobs (files) in the container
        blobs = container_client.list_blobs()
 
        # Delete each blob in the container
        for blob in blobs:
            container_client.delete_blob(blob.name)
 
        return ("All files in the container have been deleted.")
    except Exception as e:
        return (f"Error: {str(e)}")