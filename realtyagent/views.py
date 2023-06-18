import os
from pathlib import Path

from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView
from .models import Organization
from .secret import API_KEY
import openai
openai.api_key = API_KEY
os.environ['OPENAI_API_KEY'] = API_KEY

from llama_index import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage, LLMPredictor, load_graph_from_storage
from llama_index.chat_engine.condense_question import CondenseQuestionChatEngine
from langchain.chat_models import ChatOpenAI
from llama_index.indices.composability import ComposableGraph
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.agents import initialize_agent

from llama_index.langchain_helpers.agents import LlamaToolkit, create_llama_chat_agent, IndexToolConfig
from llama_index.indices.query.query_transform.base import DecomposeQueryTransform
from llama_index.query_engine.transform_query_engine import TransformQueryEngine
from langchain.chat_models import ChatOpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
chat_engine = None

def setup_chat_engine():

    storage_context_root = StorageContext.from_defaults(persist_dir='./storage/root/')
    root_id = None
    with open('root_id.txt', 'r') as file:
        root_id = file.readline()
    graph = load_graph_from_storage(
        storage_context=storage_context_root,
        root_id=root_id
    )
    # define a decompose transform
    llm_predictor = LLMPredictor(llm=ChatOpenAI(model='gpt-4'))
    decompose_transform = DecomposeQueryTransform(
        llm_predictor, verbose=True
    )

    # define custom retrievers
    keys = ['2021', '2022', '2023', 'domain_knowledge', 'Listing']
    dirs = ['./storage/' + d for d in keys]
    
    index_set = {}
    for i, d in enumerate(dirs):
        storage_context = StorageContext.from_defaults(persist_dir=d)
        index_set[keys[i]] = load_index_from_storage(storage_context=storage_context)

    custom_query_engines = {}
    for index in index_set.values():
        query_engine = index.as_query_engine()
        query_engine = TransformQueryEngine(
            query_engine,
            query_transform=decompose_transform,
            transform_extra_info={'index_summary': index.index_struct.summary},
        )
        custom_query_engines[index.index_id] = query_engine
    custom_query_engines[graph.root_id] = graph.root_index.as_query_engine(
        response_mode='tree_summarize',
        verbose=True,
    )

    # construct query engine
    graph_query_engine = graph.as_query_engine(custom_query_engines=custom_query_engines)

    # tool config
    graph_config = IndexToolConfig(
        query_engine=graph_query_engine,
        name=f"Graph Index",
        description="useful for when you want to answer queries that require analyzing San Jose housing.",
        tool_kwargs={"return_direct": True}
    )

    # define toolkit
    index_configs = []
    for y in range(2021, 2024):
        query_engine = index_set[str(y)].as_query_engine(
            similarity_top_k=3,
        )
        tool_config = IndexToolConfig(
            query_engine=query_engine, 
            name=f"Vector Index {y}",
            description=f"useful for when you want to answer queries about the {y} San Jose housing",
            tool_kwargs={"return_direct": True}
        )
        index_configs.append(tool_config)

    cons = 'domain_knowledge'
    query_engine = index_set[cons].as_query_engine()
    tool_config = IndexToolConfig(
        query_engine=query_engine, 
        name=f"Vector Index {cons}",
        description=f"useful for when you want to answer queries about the specific listing agent preferences San Jose housing",
        tool_kwargs={"return_direct": True}
    )
    index_configs.append(tool_config)

    cons = 'Listing'
    query_engine = index_set[cons].as_query_engine()
    tool_config = IndexToolConfig(
        query_engine=query_engine, 
        name=f"Vector Index {cons}",
        description=f"useful for when you want to answer queries about which homes in San Jose are on sale or on listing or available for buying",
        tool_kwargs={"return_direct": True}
    )
    index_configs.append(tool_config)

    toolkit = LlamaToolkit(
        index_configs=index_configs + [graph_config],
    )

    memory = ConversationBufferMemory(memory_key="chat_history")
    llm=ChatOpenAI(model='gpt-4')
    agent_chain = create_llama_chat_agent(
        toolkit,
        llm,
        memory=memory,
        verbose=True
    )

    return agent_chain

def login(request): 
    return render(request, 'realtyagent/login.html', {})

def chat(request):  
    if request.method == 'POST':
        conversation = request.session.get('conversation', [])
        prompt = request.POST.get('message')
        
        conversation.append({
            "role": "user",
            "content": prompt
        })
        
        completion = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = conversation
        )

        response = completion.choices[0].message
        print(response)
        conversation.append(response)
        request.session['conversation'] = conversation
        return JsonResponse(response)
    else:
        request.session['conversation'] = [
            {"role" : "assistant", "content": "You are now chatting with a user, provide them with comprehensive, short and concise answers."},
        ]
        
        return render(request, 'realtyagent/chat.html', {})

def llama_chat(request):
    global chat_engine
    if request.method == 'POST':
        if not chat_engine:
            chat_engine = setup_chat_engine()
        prompt = request.POST.get('message')


        response = chat_engine.run(prompt)
        print('Response', response)
        return JsonResponse({'content' : response})
    else:
        # Remove this when demo
        chat_engine = setup_chat_engine()
        return render(request, 'realtyagent/chat.html', {})

class OrganizationListView(ListView):
    model = Organization
    context_object_name = 'organizations'
    template_name = 'realtyagent/organizations_list.html'

class OrganizationDetailView(DetailView):
    model = Organization
    context_object_name = 'organization'


def upload(request): 
    if request.method == 'POST':
        return redirect('chat')

    return render(request, 'realtyagent/upload.html', {})

def page(request): 
    return render(request, 'realtyagent/front_page.html', {} )
    