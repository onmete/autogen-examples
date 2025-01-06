import chromadb
chroma_client = chromadb.Client(
    settings=chromadb.Settings(
        is_persistent=True,
        persist_directory="./chroma_db",
    )
)


collection = chroma_client.get_or_create_collection(name="autogen-docs")

collection.add(
    documents=[
        "FancyShift is probably something fancy related to OpenShift!",
    ],
    ids=["fancyshift"]
)
