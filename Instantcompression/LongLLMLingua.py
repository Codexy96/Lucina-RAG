from llmlingua import PromptCompressor
prompt_list=[
    "The quick brown fox jumps over the lazy dog.",
    "The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.",
    "The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.",
]
question = "What is the quick brown fox?"
llm_lingua = PromptCompressor("Qwen/Qwen2-0.5B")
compressed_prompt = llm_lingua.compress_prompt(
    prompt_list,
    question=question,
    #ratio=0.55,
    # Set the special parameter for LongLLMLingua
    condition_in_question="after_condition",
    reorder_context="sort",
    dynamic_context_compression_ratio=0.3, # or 0.4
    condition_compare=True,
    context_budget="+100",
    rank_method="longllmlingua",
)