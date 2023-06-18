import os
from pathlib import Path
from langchain import OpenAI

from secret import API_KEY
import openai
openai.api_key = API_KEY
os.environ['OPENAI_API_KEY'] = API_KEY
from collections import defaultdict
from llama_index.node_parser import SimpleNodeParser
from llama_index import SimpleDirectoryReader, VectorStoreIndex, StorageContext, download_loader, ServiceContext
from llama_index import ListIndex, LLMPredictor, ServiceContext, load_graph_from_storage
from langchain.chat_models import ChatOpenAI
from llama_index.indices.composability import ComposableGraph

BASE_DIR = Path(__file__).resolve().parent.parent
def main(): 

    index_docs = defaultdict()
    all_docs = []
    parser = SimpleNodeParser()
    dirs = os.listdir('./data/')

    for val in dirs:
        if val == '.DS_Store':
            continue
        docs = SimpleDirectoryReader(f'./data/{val}').load_data()
        index_docs[val] = parser.get_nodes_from_documents(docs)
        all_docs.extend(docs)

    llm_predictor = LLMPredictor(llm=ChatOpenAI(model='gpt-4'))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
    index_set = defaultdict()
    for val in index_docs.keys():
        storage_context = StorageContext.from_defaults()
        cur_index = VectorStoreIndex.from_documents(index_docs[val], storage_context=storage_context, service_context=service_context)
        index_set[val] = cur_index
        storage_context.persist(persist_dir=f'./storage/{val}')

    
    years = [2023, 2022, 2021]
    index_summaries = [f"San Jose houing report for {year} fiscal year" for year in years]
    # Transactions
    index_summaries.append('Transactions that user made during so far. Useful for analyze agent income, volumn of sales made so far.')
    # Listing
    index_summaries.append('This is a current home for sales')
    # Knowledge
    index_summaries.append('This is what we know about some listing agents\' preferences and special zip codes')
    
    storage_context = StorageContext.from_defaults()
    children_indices = [index_set[val] for val in sorted(index_set.keys())]
    print(index_set.keys())

    graph = ComposableGraph.from_indices(
        ListIndex,
        children_indices,
        index_summaries=index_summaries,
        service_context=service_context,
        storage_context=storage_context,
    )

    root_id = graph.root_id
    storage_context.persist(persist_dir='./storage/root')

    with open('root_id.txt', 'w') as file:
        file.write(root_id)

    # data = BASE_DIR / 'data/'
    
    # documents = []
    # storage_context = StorageContext.from_defaults()

    # # process years data.
    # for y in range(2021, 2024):
    #     document = SimpleDirectoryReader(f'data/{y}').load_data()
    #     for d in document:
    #         d.extra_info = {f"summary" : "market report from San Jose city for year {y}"}
    #     documents.extend(document)
    
    # # process domain knowledge
    # DocxReader = download_loader("DocxReader")
    # loader = DocxReader()
    # document = loader.load_data(file=Path('data/domain_knowledge/Property_Address.docx'))
    # for d in document:
    #     d.extra_info = {
    #         "description": "The preferences of listing agents."
    #     }
    # documents.extend(document)

    # # load listing
    # document = SimpleDirectoryReader('data/Listing').load_data()
    # for d in document:
    #     d.extra_info = {
    #         "description": "Homes that are available on market"
    #     }

    # documents.extend(document)

    # indexed_docs = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
    # storage_context.persist(persist_dir=f'./storage')

    # this is chatgpt
    #service_context = ServiceContext.from_defaults(llm=ChatOpenAI(temperature=0.56))

    #return indexed_docs.as_chat_engine(service_context=service_context,)
    # return indexed_docs.as_chat_engine()


if __name__ == "__main__":
    main()