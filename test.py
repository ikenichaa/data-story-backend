from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_ollama import OllamaLLM
from langchain_core.runnables import RunnableLambda


if __name__ == "__main__":
    model = OllamaLLM(
        model="deepseek-r1:7b",
    ) 


    def add_one(x: int) -> int:
        return x + 1

    def mul_two(x: int) -> int:
        return x * 2

    def mul_three(x: int) -> int:
        return x * 3

    runnable_1 = RunnableLambda(add_one)
    runnable_2 = RunnableLambda(mul_two)
    runnable_3 = RunnableLambda(mul_three)

    sequence = runnable_1 | {  # this dict is coerced to a RunnableParallel
        "mul_two": runnable_2,
        "mul_three": runnable_3,
    }

    res = sequence.invoke(1)
    print(res) 

    res = sequence.batch([1, 2, 3])
    print(res)

    joke_chain = (
    ChatPromptTemplate.from_template("tell me a joke about bear")
    | model
    )

    poem_chain = (
        ChatPromptTemplate.from_template("write a 2-line poem about bear")
        | model
    )

    runnable = RunnableParallel(joke=joke_chain, poem=poem_chain)

    output = {"joke": "", "poem": ""}
    for chunk in runnable.stream({}):
        print(chunk)
        for key in chunk:
            print(f"{key}: {chunk}")
            output[key] += chunk[key]
            print("-----")
    # print(output)
