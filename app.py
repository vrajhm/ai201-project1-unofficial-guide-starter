import gradio as gr

from query import ask


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {source}" for source in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown("# The Unofficial Guide\nAsk questions about campus dining — answers are grounded in student reviews.")
    inp = gr.Textbox(label="Your question", placeholder="Which dining hall has the shortest lunch wait?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")
