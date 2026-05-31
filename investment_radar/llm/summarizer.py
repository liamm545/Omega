def summarize_news_with_llm(news_rows, client=None):
    """TODO: plug OpenAI client. MVP returns source-bound summaries from sample rows."""
    return [row.get("summary", "missing") for row in news_rows]
