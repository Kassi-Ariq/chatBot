import ollama
import chromadb

def get_relevant_items(client, items, prompt, collection_name, size, model="all-minilm"):


    

 
    if collection_name in client.list_collections():
        client.delete_collection(collection_name)
        
    collection = client.create_collection(collection_name)


    for i, item in enumerate(items):
        response = ollama.embeddings(model=model, prompt=item)
        embedding = response["embedding"]
        collection.add(
            ids=[str(i)],
            embeddings=[embedding],
            documents=[item]
        )


    response = ollama.embeddings(prompt=prompt, model=model)

    results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=size  
    )

    return results['documents'][0]

def getRelevantData(client, searchResults, prompt):
    return get_relevant_items(client, searchResults, prompt, collection_name="search_results", size=5)

def getRelevantImages(images, prompt):
    images_alt = [img[1] for img in images] 
    image_urls = [img[0] for img in images]  

    relevant_alts = get_relevant_items(images_alt, prompt, collection_name="images", size=6, model="all-minilm")

    relevant_image_urls = [image_urls[images_alt.index(alt)] for alt in relevant_alts]
    
    return relevant_image_urls