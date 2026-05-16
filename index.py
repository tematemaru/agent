from agent import Agent


def main():

    agent = Agent(
        model_name="qwen3:4b",
        embed_model="nomic-embed-text",
    )

    agent.run()


if __name__ == "__main__":
    main()